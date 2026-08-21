#!/usr/bin/env python3
"""Verify that commands and paths cited in agent docs actually exist.

Agent docs (AGENTS.md, CLAUDE.md, nested variants, docs/) guide agents that
copy commands verbatim and follow paths literally. Nothing executes prose, so
nothing catches its drift — a renamed script or removed make target silently
sends every future agent session down a broken path. This check makes that
drift mechanical: it extracts backtick-quoted commands, path references, and
relative markdown links from the docs and verifies each against the repo.

What is checked
- task-runner invocations resolve: `npm run X` / `npm test` / `yarn|pnpm run X`
  against package.json scripts, `make X` against Makefile targets, `just X`
  against justfile recipes
- script invocations point at existing files: `python foo.py`, `node foo.js`,
  `bash foo.sh`, `./foo`
- backtick-quoted repo paths exist (root-relative or doc-relative)
- relative markdown link targets exist
- exec-plan frontmatter graph edges (`depends-on`, `discovered-from`) name
  plan files that exist under docs/exec-plans/
- ADR frontmatter lifecycle: `superseded-by` targets exist, `status:
  superseded` and `superseded-by` appear together, and root instruction files
  (AGENTS.md, CLAUDE.md, …) cite only accepted ADRs
- first tokens of shell-block commands resolve on PATH (warning only — the
  environment running this check may legitimately differ)

The matcher is conservative by design: false negatives over false positives.
Tokens with placeholders (<...>, {...}, $VAR, *), URLs, absolute paths, and
build-output dirs (dist/, build/, ...) are skipped. A clean run therefore does
not prove the docs are complete — only that nothing cited is verifiably dead.

Usage
    check_docs.py [REPO_ROOT]            # discover and check agent docs
    check_docs.py FILE.md [FILE.md ...]  # check specific files
    check_docs.py --strict ...           # promote warnings to errors
Exit code: 1 if any error (CI-gate ready), 0 otherwise.

To install as a CI gate, copy this file into the target repo (e.g. scripts/)
and add a job step:  python3 scripts/check_docs.py .
Python 3.8+, stdlib only.
"""

import argparse
import difflib
import json
import re
import shutil
import sys
from pathlib import Path

SHELL_LANGS = {"sh", "bash", "shell", "zsh", "console", "terminal"}
SKIP_CHARS = set("<>{}$*?")
BUILD_DIRS = {"dist", "build", "out", "target", "node_modules", ".venv", "venv",
              "coverage", "tmp", "__pycache__", ".next", "vendor"}
KNOWN_EXTS = {"md", "py", "js", "ts", "tsx", "jsx", "mjs", "cjs", "json", "yml",
              "yaml", "toml", "sh", "txt", "cfg", "ini", "lock", "mk", "go",
              "rs", "java", "rb", "css", "html", "sql", "csv", "env", "xml"}
KNOWN_FILES = {"Makefile", "makefile", "justfile", "Justfile", "Dockerfile",
               "LICENSE", "CODEOWNERS", "Taskfile"}
SHELL_BUILTINS = {"cd", "export", "source", "echo", "set", "exit", "true",
                  "false", "alias", "unset", "eval", "exec", "trap", "wait",
                  "if", "then", "else", "fi", "for", "while", "do", "done",
                  "case", "esac", "time", "env", "sudo", "watch", "xargs"}
DOC_NAMES = {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "GEMINI.md"}

INLINE_CODE = re.compile(r"`([^`\n]+)`")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
ADR_STATUSES = {"proposed", "accepted", "superseded"}
ADR_REF = re.compile(r"\bADR-?(\d{1,6})\b", re.IGNORECASE)


def parse_frontmatter(lines):
    """Minimal YAML-subset frontmatter parser: flat keys with scalar,
    [inline]-list, or dash-list values, plus comments. Returns
    ({key: ([values], lineno)}, closing_line) — values always a list, empty
    for blank scalars — or (None, 0) when there is no terminated frontmatter
    block. Deliberately not a YAML implementation: the doc graph needs only
    flat keys, and a parser dependency would break the stdlib-only contract."""
    if not lines or lines[0].strip() != "---":
        return None, 0
    data, key = {}, None
    for i, raw in enumerate(lines[1:], start=2):
        if raw.strip() == "---":
            return data, i
        line = re.sub(r"\s+#.*$", "", raw).rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        d = re.match(r"^\s*-\s+(.+)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                items = [v.strip().strip("'\"") for v in val[1:-1].split(",")]
                data[key] = ([v for v in items if v], i)
            else:
                data[key] = ([val.strip("'\"")] if val else [], i)
        elif d and key is not None:
            data[key][0].append(d.group(1).strip().strip("'\""))
    return None, 0  # unterminated — treat the file as having no frontmatter


WHY_DEAD_REF = ("agents copy commands from docs verbatim and follow paths "
                "literally; a dead reference sends every future session down a "
                "broken path before it writes any code.")
WHY_DOC_GRAPH = ("the frontmatter graph is the agents' task and decision "
                 "memory; a broken edge or stale status makes future sessions "
                 "trust decisions that no longer hold or wait on work that "
                 "doesn't exist.")


class Finding:
    def __init__(self, level, path, line, cited, problem, fix, why=WHY_DEAD_REF):
        self.level, self.path, self.line = level, path, line
        self.cited, self.problem, self.fix, self.why = cited, problem, fix, why

    def render(self):
        mark = "✖" if self.level == "error" else "⚠"
        return (f"{mark} {self.path}:{self.line} — `{self.cited}` — {self.problem}\n"
                f"  Why this matters: {self.why}\n"
                f"  Fix: {self.fix}")


def discover_docs(root: Path):
    docs = []
    for pattern in ("AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "GEMINI.md",
                    "**/AGENTS.md", "**/CLAUDE.md",
                    ".github/copilot-instructions.md", ".claude/rules/*.md",
                    "docs/**/*.md"):
        for p in root.glob(pattern):
            if p.is_file() and not any(part in BUILD_DIRS or part == ".git"
                                       for part in p.parts):
                docs.append(p)
    return sorted(set(docs))


def load_scripts(candidates):
    """Union of package.json script names from the given directories."""
    scripts = {}
    for d in candidates:
        pkg = d / "package.json"
        if pkg.is_file():
            try:
                scripts.update(json.loads(pkg.read_text()).get("scripts", {}))
            except (json.JSONDecodeError, OSError):
                pass
    return scripts if scripts else None  # None: no package.json found at all


def load_make_targets(candidates):
    targets, found = set(), False
    for d in candidates:
        for name in ("Makefile", "makefile", "GNUmakefile"):
            mk = d / name
            if not mk.is_file():
                continue
            found = True
            for line in mk.read_text(errors="replace").splitlines():
                m = re.match(r"^([A-Za-z0-9_./ -]+):([^=]|$)", line)
                if m and "%" not in m.group(1):
                    for t in m.group(1).split():
                        targets.add(t)
    targets.discard(".PHONY")
    return targets if found else None


def load_just_recipes(candidates):
    recipes, found = set(), False
    for d in candidates:
        for name in ("justfile", "Justfile", ".justfile"):
            jf = d / name
            if not jf.is_file():
                continue
            found = True
            for line in jf.read_text(errors="replace").splitlines():
                # Params may carry default values (build target="all":), so
                # allow "=" before the colon — but reject ":=" assignments.
                m = re.match(r"^@?([A-Za-z0-9_-]+)(\s[^:]*)?:([^=]|$)", line)
                if m:
                    recipes.add(m.group(1))
    return recipes if found else None


def path_exists(token: str, root: Path, doc_dir: Path):
    clean = token.rstrip("/").split("#")[0]
    if not clean:
        return True
    return (root / clean).exists() or (doc_dir / clean).exists()


def looks_like_path(token: str):
    """Conservative: only tokens we are confident are meant as repo paths.

    Bare filenames without a slash (`Makefile`, `CLAUDE.md`) are deliberately
    NOT checked: prose routinely mentions kinds of files generically, which is
    no claim that this repo contains one. Slash paths assert a location.
    """
    if (not token or token[0] in "-#" or "://" in token or token.startswith("/")
            or SKIP_CHARS & set(token) or "(" in token or " " in token
            or token.startswith("http") or ".." in token or "/" not in token):
        return False
    if token.startswith("./"):
        return True
    base = token.rstrip("/")
    last = base.split("/")[-1]
    if last in KNOWN_FILES or token.endswith("/"):
        return True
    ext = last.rsplit(".", 1)[-1] if "." in last else ""
    return ext.lower() in KNOWN_EXTS


def first_segment_anchored(token: str, root: Path, doc_dir: Path):
    """For slash paths: only judge tokens whose first segment exists as a dir
    (otherwise it may be a MIME type, URL fragment, etc. — skip)."""
    seg = token.lstrip("./").split("/")[0]
    if seg in BUILD_DIRS:
        return False
    return token.startswith("./") or (root / seg).is_dir() or (doc_dir / seg).is_dir()


def suggest(name, pool):
    close = difflib.get_close_matches(name, pool or [], n=1)
    return f' (closest existing: "{close[0]}")' if close else ""


def resolve_adr(adr_dir: Path, token: str):
    """Resolve a superseded-by value — filename, stem, or ADR-NNNN — to a file."""
    stem = token[:-3] if token.endswith(".md") else token
    pool = {p.stem: p for p in adr_dir.glob("*.md")}
    if stem in pool:
        return pool[stem]
    m = re.fullmatch(r"(?i)(?:adr-?)?0*(\d+)", stem)
    if m:
        for s, p in pool.items():
            dm = re.match(r"\d+", s)
            if dm and int(dm.group(0)) == int(m.group(1)):
                return p
    return None


class Checker:
    def __init__(self, root: Path):
        self.root = root
        self.findings = []
        self.checked = 0
        self._adr_index = None

    def check_file(self, doc: Path):
        doc_dir = doc.parent
        ctx = [self.root, doc_dir]
        npm = load_scripts(ctx)
        make = load_make_targets(ctx)
        just = load_just_recipes(ctx)
        rel = doc.relative_to(self.root) if self.root in doc.parents or doc.parent == self.root else doc

        lines = doc.read_text(errors="replace").splitlines()
        fm, fm_end = parse_frontmatter(lines)
        if fm:
            self.check_frontmatter(doc, rel, fm)
        root_doc = doc.name in DOC_NAMES

        in_fence, fence_lang, prev_continued = False, "", False
        for lineno, line in enumerate(lines, 1):
            if lineno <= fm_end:
                continue
            fence = re.match(r"^\s*(```+|~~~+)\s*(\w*)", line)
            if fence:
                in_fence = not in_fence
                fence_lang = fence.group(2).lower() if in_fence else ""
                prev_continued = False
                continue
            if in_fence:
                if fence_lang in SHELL_LANGS:
                    if prev_continued:
                        prev_continued = line.rstrip().endswith("\\")
                        continue
                    prev_continued = line.rstrip().endswith("\\")
                    self.check_command_line(line, rel, lineno, doc_dir, npm, make, just,
                                            which_check=True)
                continue
            for m in INLINE_CODE.finditer(line):
                span = m.group(1).strip()
                if " " in span:
                    self.check_command_line(span, rel, lineno, doc_dir, npm, make, just,
                                            which_check=False)
                elif looks_like_path(span):
                    self.check_path(span, rel, lineno, doc_dir)
            for m in MD_LINK.finditer(line):
                target = m.group(1)
                if (not target.startswith(("http", "mailto:", "#", "/"))
                        and not SKIP_CHARS & set(target)):
                    clean = target.split("#")[0]
                    if clean and not (doc_dir / clean).exists() and not (self.root / clean).exists():
                        self.checked += 1
                        self.findings.append(Finding(
                            "error", rel, lineno, target,
                            "this link target does not exist.",
                            "fix the link, restore the file, or drop the reference."))
                    elif clean:
                        self.checked += 1
            if root_doc:
                self.check_adr_refs(line, rel, lineno)

    # --- frontmatter graph checks (exec plans, ADRs) ---

    def check_frontmatter(self, doc, rel, fm):
        if "exec-plans" in doc.parts:
            self.check_plan_frontmatter(doc, rel, fm)
        elif doc.parent.name == "adr":
            self.check_adr_frontmatter(doc, rel, fm)

    def check_plan_frontmatter(self, doc, rel, fm):
        plans_root = Path(*doc.parts[:doc.parts.index("exec-plans") + 1])
        pool = set()
        for p in plans_root.rglob("*.md"):
            pool.update((p.stem, p.name))
        for key in ("depends-on", "discovered-from"):
            targets, lineno = fm.get(key, ([], 0))
            for t in targets:
                if SKIP_CHARS & set(t):
                    continue
                self.checked += 1
                if t not in pool:
                    self.findings.append(Finding(
                        "error", rel, lineno, f"{key}: {t}",
                        f'no exec plan named "{t}" exists under '
                        f"{plans_root.name}/{suggest(t, pool)}.",
                        "correct the reference, or create the plan it points "
                        "at — a dead graph edge blocks ready-work computation.",
                    WHY_DOC_GRAPH))

    def check_adr_frontmatter(self, doc, rel, fm):
        status_vals, status_line = fm.get("status", ([], 0))
        status = status_vals[0].lower() if status_vals else None
        sup_vals, sup_line = fm.get("superseded-by", ([], 0))
        sup = sup_vals[0] if sup_vals else None
        if status is not None:
            self.checked += 1
            if status not in ADR_STATUSES:
                self.findings.append(Finding(
                    "warning", rel, status_line, f"status: {status}",
                    "not a lifecycle status this docs system uses "
                    "(proposed | accepted | superseded).",
                    "map onto a standard status so lifecycle checks stay "
                    "mechanical.",
                    WHY_DOC_GRAPH))
        if status == "superseded" and not sup:
            self.findings.append(Finding(
                "error", rel, status_line, "status: superseded",
                "status is superseded but superseded-by names no ADR.",
                "point superseded-by at the replacing ADR — without the edge, "
                "agents cannot follow the decision to its current form.",
                    WHY_DOC_GRAPH))
        if sup and status != "superseded":
            self.findings.append(Finding(
                "error", rel, sup_line, f"superseded-by: {sup}",
                f'superseded-by is set but status is "{status or "missing"}".',
                "set status: superseded, or clear superseded-by — the two "
                "must appear together.",
                    WHY_DOC_GRAPH))
        if sup and not (SKIP_CHARS & set(sup)):
            self.checked += 1
            if resolve_adr(doc.parent, sup) is None:
                pool = [p.stem for p in doc.parent.glob("*.md")]
                self.findings.append(Finding(
                    "error", rel, sup_line, f"superseded-by: {sup}",
                    f"no such ADR exists in {doc.parent.name}/"
                    f"{suggest(sup, pool)}.",
                    "correct the reference, or add the superseding ADR.",
                    WHY_DOC_GRAPH))

    def adr_status_index(self):
        """ADR number → (filename, status) for docs/adr/ at the repo root."""
        if self._adr_index is None:
            self._adr_index = {}
            for p in sorted((self.root / "docs" / "adr").glob("*.md")):
                m = re.match(r"\d+", p.stem)
                if not m:
                    continue
                fm, _ = parse_frontmatter(p.read_text(errors="replace").splitlines())
                vals = (fm or {}).get("status", ([], 0))[0]
                status = vals[0].lower() if vals else None
                self._adr_index[int(m.group(0))] = (p.name, status)
        return self._adr_index

    def check_adr_refs(self, line, rel, lineno):
        if not (self.root / "docs" / "adr").is_dir():
            return
        for m in ADR_REF.finditer(line):
            self.checked += 1
            entry = self.adr_status_index().get(int(m.group(1)))
            if entry is None:
                self.findings.append(Finding(
                    "error", rel, lineno, m.group(0),
                    "no ADR with this number exists in docs/adr/.",
                    "correct the number, or add the missing decision record.",
                    WHY_DOC_GRAPH))
            elif entry[1] == "superseded":
                self.findings.append(Finding(
                    "error", rel, lineno, m.group(0),
                    f"{entry[0]} is superseded — root instruction files must "
                    "cite only accepted ADRs.",
                    "point at the superseding ADR instead, or drop the "
                    "reference.",
                    WHY_DOC_GRAPH))
            elif entry[1] == "proposed":
                self.findings.append(Finding(
                    "warning", rel, lineno, m.group(0),
                    f"{entry[0]} is still proposed, not accepted.",
                    "accept the ADR before citing it as binding guidance, or "
                    "mark the reference as tentative.",
                    WHY_DOC_GRAPH))

    def check_path(self, token, rel, lineno, doc_dir):
        # Slash tokens are only judged when their first segment is a real
        # directory (else `application/json` and friends false-positive) —
        # except .md references, which are unambiguous doc cross-links.
        if ("/" in token and not token.endswith(".md")
                and not first_segment_anchored(token, self.root, doc_dir)):
            return
        if "/" in token and token.lstrip("./").split("/")[0] in BUILD_DIRS:
            return
        self.checked += 1
        if not path_exists(token, self.root, doc_dir):
            self.findings.append(Finding(
                "error", rel, lineno, token, "this path does not exist in the repo.",
                "correct the path, restore the file, or remove the stale reference."))

    def check_command_line(self, line, rel, lineno, doc_dir, npm, make, just,
                           which_check):
        text = line.strip()
        if not text or text.startswith("#"):
            return
        text = re.sub(r"^\$\s+", "", text)
        for part in re.split(r"&&|\|\||;|\|", text):
            tokens = part.strip().split()
            tokens = [t for t in tokens if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t)]
            if not tokens:
                continue
            head = tokens[0]
            if SKIP_CHARS & set(part):
                continue
            self.check_runner(tokens, rel, lineno, npm, make, just)
            if head in ("python", "python3", "node", "bash", "sh", "ruby") and len(tokens) > 1:
                arg = next((t for t in tokens[1:] if not t.startswith("-")), None)
                if arg and looks_like_path(arg):
                    self.check_path(arg, rel, lineno, doc_dir)
            elif head.startswith("./"):
                self.check_path(head, rel, lineno, doc_dir)
            elif (which_check and head not in SHELL_BUILTINS and "/" not in head
                  and head.isascii() and re.fullmatch(r"[A-Za-z0-9_.+-]+", head)):
                self.checked += 1
                if shutil.which(head) is None:
                    self.findings.append(Finding(
                        "warning", rel, lineno, head,
                        "this executable is not on PATH here.",
                        "if the tool is a real prerequisite, document how to "
                        "install it (or add it to the bootstrap command); if "
                        "the command is stale, remove it. Ignore if this "
                        "environment legitimately lacks the tool."))

    def check_runner(self, tokens, rel, lineno, npm, make, just):
        head, rest = tokens[0], tokens[1:]
        def fail(cited, problem, fix):
            self.findings.append(Finding("error", rel, lineno, cited, problem, fix))

        if head in ("npm", "yarn", "pnpm"):
            script = None
            if rest[:1] == ["run"] and len(rest) > 1:
                script = rest[1]
            elif rest[:1] == ["test"]:
                script = "test"
            if script and npm is not None:
                self.checked += 1
                if script not in npm:
                    fail(f"{head} {'run ' if rest[:1] == ['run'] else ''}{script}",
                         f'package.json has no script "{script}"{suggest(script, npm)}.',
                         "correct the doc to a script that exists, or add the "
                         "missing script to package.json.")
            elif script and npm is None:
                self.findings.append(Finding(
                    "warning", rel, lineno, f"{head} … {script}",
                    "no package.json found next to this doc or at the repo root.",
                    "remove the command, fix the working-directory context, or "
                    "add the package.json it refers to."))
        elif head == "make" and rest:
            target = next((t for t in rest if not t.startswith("-") and "=" not in t), None)
            if target:
                self.checked += 1
                if make is None:
                    self.findings.append(Finding(
                        "warning", rel, lineno, f"make {target}",
                        "no Makefile found next to this doc or at the repo root.",
                        "remove the command, fix the working-directory context, "
                        "or add the Makefile."))
                elif target not in make:
                    fail(f"make {target}",
                         f'the Makefile has no target "{target}"{suggest(target, make)}.',
                         "correct the doc to an existing target, or add the target.")
        elif head == "just" and rest:
            target = next((t for t in rest if not t.startswith("-")), None)
            if target:
                self.checked += 1
                if just is None:
                    self.findings.append(Finding(
                        "warning", rel, lineno, f"just {target}",
                        "no justfile found next to this doc or at the repo root.",
                        "remove the command or add the justfile."))
                elif target not in just:
                    fail(f"just {target}",
                         f'the justfile has no recipe "{target}"{suggest(target, just)}.',
                         "correct the doc to an existing recipe, or add the recipe.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", default=["."],
                    help="repo root (default .) or explicit .md files")
    ap.add_argument("--strict", action="store_true",
                    help="treat warnings (PATH lookups, missing Makefile) as errors")
    args = ap.parse_args()

    paths = [Path(p).resolve() for p in (args.paths or ["."])]
    if len(paths) == 1 and paths[0].is_dir():
        root, docs = paths[0], discover_docs(paths[0])
    else:
        files = [p for p in paths if p.is_file()]
        if len(files) != len(paths):
            missing = [str(p) for p in paths if not p.is_file()]
            print(f"error: not a file: {', '.join(missing)}", file=sys.stderr)
            return 2
        root, docs = Path.cwd().resolve(), files

    if not docs:
        print(f"check_docs: no agent docs found under {root} — nothing to check.")
        return 0

    checker = Checker(root)
    for doc in docs:
        checker.check_file(doc)

    errors = [f for f in checker.findings if f.level == "error"]
    warnings = [f for f in checker.findings if f.level == "warning"]
    for f in errors + warnings:
        print(f.render(), end="\n\n")
    print(f"check_docs: {len(docs)} doc(s), {checker.checked} reference(s) checked — "
          f"{len(errors)} error(s), {len(warnings)} warning(s).")
    if errors or (args.strict and warnings):
        print("Result: FAIL — the docs cite things that don't exist; fix the "
              "docs or the repo so agents stop inheriting dead instructions.")
        return 1
    print("Result: OK — nothing cited in the docs is verifiably dead. (This "
          "check is conservative: it proves cited things exist, not that the "
          "docs are complete or semantically current.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
