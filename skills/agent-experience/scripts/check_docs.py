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


class Finding:
    def __init__(self, level, path, line, cited, problem, fix):
        self.level, self.path, self.line = level, path, line
        self.cited, self.problem, self.fix = cited, problem, fix

    def render(self):
        mark = "✖" if self.level == "error" else "⚠"
        why = ("agents copy commands from docs verbatim and follow paths "
               "literally; a dead reference sends every future session down a "
               "broken path before it writes any code.")
        return (f"{mark} {self.path}:{self.line} — `{self.cited}` — {self.problem}\n"
                f"  Why this matters: {why}\n"
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
                m = re.match(r"^@?([A-Za-z0-9_-]+)(\s[^:=]*)?:", line)
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


class Checker:
    def __init__(self, root: Path):
        self.root = root
        self.findings = []
        self.checked = 0

    def check_file(self, doc: Path):
        doc_dir = doc.parent
        ctx = [self.root, doc_dir]
        npm = load_scripts(ctx)
        make = load_make_targets(ctx)
        just = load_just_recipes(ctx)
        rel = doc.relative_to(self.root) if self.root in doc.parents or doc.parent == self.root else doc

        in_fence, fence_lang, prev_continued = False, "", False
        for lineno, line in enumerate(doc.read_text(errors="replace").splitlines(), 1):
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
