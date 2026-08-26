#!/usr/bin/env python3
"""Verify that commands and paths cited in agent docs actually exist.

Agent docs (AGENTS.md, CLAUDE.md, nested variants, docs/) guide agents that
copy commands verbatim and follow paths literally. Nothing executes prose, so
nothing catches its drift — a renamed script or removed make target silently
sends every future agent session down a broken path. This check makes that
drift mechanical: it extracts backtick-quoted commands, path references, and
relative markdown links from the docs and verifies each against the repo.

What is checked
- task-runner invocations resolve: `npm run X` / `npm test|start` /
  `yarn|pnpm run X` against package.json scripts — workspace-targeted forms
  (`npm run X -w ws`, `pnpm --filter ws run X`, `yarn workspace ws run X`,
  and yarn's run-less shorthand `yarn workspace ws X`) against the named
  workspace's package.json. A yarn workspace name that matches no package is
  itself an error — the value is positional and unambiguous. A shorthand
  token that is neither a script nor a findable binary is a warning, not an
  error, because the binary may simply not be installed here
- script invocations point at existing files: `python foo.py`, `node foo.js`,
  `bash foo.sh`, `./foo`
- backtick-quoted repo paths exist (root-relative or doc-relative)
- cross-repo references written as `repo:path` (backticked or as link
  targets) resolve inside a sibling checkout `../repo` when one exists, and
  are skipped otherwise — the explicit form also keeps a sibling-repo path
  from being mistaken for (or coincidentally matching) a local one
- relative markdown link targets exist
- intra-document anchor links (`[…](#section)`) resolve to a heading or
  explicit id in the same file
- directional prose pointers ("see the open questions below") point at
  content that exists in that direction — flagged only when *none* of the
  pointer's significant words appears there, so ordinary prose never trips it
- universal claims about a directory's contents ("one test file per `src/`
  module") are flagged for enumeration — the predicate is not machine-decidable,
  so this reports the shape (quantifier + claim verb + a cited directory) as a
  warning and leaves the verdict to the author
- exec-plan frontmatter graph edges (`depends-on`, `discovered-from`,
  `relates-to`) name plan files that exist under docs/exec-plans/
- ADR frontmatter lifecycle: `superseded-by` targets exist, `status:
  superseded` and `superseded-by` appear together, and root instruction files
  (AGENTS.md, CLAUDE.md, …) cite only accepted ADRs
- first tokens of shell-block commands resolve on PATH (warning only — the
  environment running this check may legitimately differ)

The matcher is conservative by design: false negatives over false positives.
Tokens with placeholders (<...>, {...}, $VAR, *), URLs, absolute paths, and
build-output dirs (dist/, build/, ...) are skipped. A clean run therefore does
not prove the docs are complete — only that nothing cited is verifiably dead.
--verbose lists every token that was seen but deliberately not judged, with
the reason — the coverage boundary made visible, so an author can tell
"checked and fine" apart from "never checked at all".

Usage
    check_docs.py [REPO_ROOT]            # discover and check agent docs
    check_docs.py FILE.md [FILE.md ...]  # check specific files
    check_docs.py --strict ...           # promote warnings to errors
    check_docs.py --verbose ...          # also list tokens seen but not judged
    check_docs.py --exclude 'fixtures/*' .   # skip fixture docs by glob
    check_docs.py --require-docs .       # fail when no docs are found
Discovery skips gitignored files (when root is its own work tree, or a
non-ignored directory inside one) and any repo-relative path matched by an
--exclude glob — deliberately-broken fixtures and generated workspaces would
otherwise fail the check. Files named explicitly on the command line are
always checked. If filtering removes every doc it found, that is an error
rather than a quiet pass: a gate that discovers nothing reports success
forever.
Exit code: 1 if any error, 0 otherwise.

Run this script from the skill against the target repo — do not copy it into
target repos: a copy stops evolving with the original. (Distribution through a
package registry, so CI could install it, is future work.) On a re-audit of a
repo known to have agent docs, add --require-docs so a run that checks nothing
fails: without it, deleting or renaming the last agent doc returns the check
to "nothing to check", exit 0, forever.
Python 3.8+, stdlib only.
"""

import argparse
import difflib
import fnmatch
import json
import os
import re
import shutil
import subprocess
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
# Yarn built-in subcommands that may legitimately follow `yarn workspace ws`
# without naming a package.json script (`yarn workspace ws add lodash`).
# Anything else in that position is yarn's run-less script/binary shorthand.
YARN_COMMANDS = {"add", "remove", "upgrade", "upgrade-interactive", "up",
                 "link", "unlink", "pack", "publish", "version", "versions",
                 "info", "install", "audit", "outdated", "why", "licenses",
                 "list", "exec", "node", "dlx", "bin", "cache", "config",
                 "set", "run", "create", "init", "import", "help", "global",
                 "workspace", "workspaces", "focus"}
DOC_NAMES = {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "GEMINI.md"}

INLINE_CODE = re.compile(r"`([^`\n]+)`")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
ADR_STATUSES = {"proposed", "accepted", "superseded"}
ADR_REF = re.compile(r"\bADR-?(\d{1,6})\b", re.IGNORECASE)
HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$")
SETEXT_UNDERLINE = re.compile(r"^ {0,3}(=+|-+)\s*$")
HTML_ID = re.compile(r'(?:id|name)="([^"]+)"')
PROSE_POINTER = re.compile(
    r"\bsee\s+(?:also\s+)?(?:the\s+)?([A-Za-z][A-Za-z0-9 _'/&-]{2,60}?)"
    r"\s+(below|above)\b", re.IGNORECASE)
WORD = re.compile(r"[A-Za-z][A-Za-z0-9'-]*")
# Words that name the *form* or *position* of pointed-at content rather than
# its subject ("see the notes below"). A pointer made only of these carries
# nothing checkable, so it is skipped rather than judged.
POINTER_STOPWORDS = {
    "the", "and", "for", "with", "from", "its", "this", "that", "these",
    "those", "them",
    "section", "sections", "subsection", "note", "notes", "item", "items",
    "list", "lists", "table", "tables", "paragraph", "paragraphs", "chapter",
    "part", "parts", "page", "pages", "example", "examples", "snippet",
    "snippets", "block", "blocks", "code", "output", "figure", "diagram",
    "screenshot", "detail", "details", "description", "discussion",
    "explanation", "instructions", "step", "steps", "comment", "comments",
    "point", "points", "entry", "entries", "line", "lines", "text",
    "full", "further", "more", "also", "above", "below", "relevant",
    "corresponding", "respective", "next", "previous", "own", "other",
    "remaining", "following", "preceding",
}

# A universal claim about a directory's contents ("every module under `src/`
# has a test") is the fabrication family that most reliably survives
# self-review: it reads as observed fact, is almost never enumerated, and
# nothing downstream re-checks it. The predicate is not decidable here, so the
# *shape* is what is flagged — quantifier + claim verb + a cited directory.
# Rules are deliberately not matched: "every new module must have a test"
# states an invariant to enforce, not an observation to verify, and modals are
# absent from the claim-verb list for exactly that reason.
GENERALIZATION = re.compile(
    r"\b(?:every|each|all)\b[^.;]{0,40}?"
    r"\b(?:is|are|has|have|contains?|includes?|exports?|lives?|gets?|uses?)\b"
    r"|\bone\b[^.;]{0,40}?\bper\b", re.IGNORECASE)
SENTENCE_SPLIT = re.compile(r"(?<=[.;])\s+")


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
WHY_DEAD_POINTER = ("a pointer to content that does not exist teaches agents "
                    "the doc cannot be trusted — every future session burns "
                    "context searching for it or, worse, invents it.")
WHY_UNVERIFIED_CLAIM = ("a universal claim reads as observed fact, and agents "
                        "that have just read a doc are measurably less likely "
                        "to verify by running things — so one counter-example "
                        "in the directory becomes ground truth every future "
                        "session inherits.")


def github_slug(text: str):
    """Anchor id the way GitHub renders a heading: inline markup stripped,
    lowercased, punctuation dropped, spaces to hyphens."""
    text = text.replace("`", "")
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_]{1,3}", "", text)
    text = re.sub(r"[^\w\- ]", "", text.strip().lower())
    return re.sub(r" ", "-", text)


def collect_anchors(lines, fm_end):
    """Anchor ids defined in a document: GitHub-style heading slugs (ATX and
    setext) plus explicit HTML id=/name= attributes. Fenced code is skipped —
    a # comment inside a code block is not a heading."""
    anchors, in_fence, prev = set(), False, ""
    for lineno, line in enumerate(lines, 1):
        if lineno <= fm_end:
            continue
        if re.match(r"^\s*(```+|~~~+)", line):
            in_fence, prev = not in_fence, ""
            continue
        if in_fence:
            continue
        m = HEADING.match(line)
        if m:
            anchors.add(github_slug(m.group(1)))
        elif SETEXT_UNDERLINE.match(line) and prev.strip():
            # May also be a thematic break after a paragraph; the extra anchor
            # that misreading adds can only silence, never raise, a finding.
            anchors.add(github_slug(prev))
        for a in HTML_ID.finditer(line):
            anchors.add(a.group(1).lower())
        prev = line
    return anchors


def significant_words(phrase: str):
    return [w for w in WORD.findall(phrase.lower())
            if len(w) >= 3 and w not in POINTER_STOPWORDS]


def word_stem(w: str):
    """Crude unifier for inflection (question/questions, handling/handled).
    Collisions only ever silence a finding, never raise one."""
    return w[:5]


class Finding:
    def __init__(self, level, path, line, cited, problem, fix, why=WHY_DEAD_REF):
        self.level, self.path, self.line = level, path, line
        self.cited, self.problem, self.fix, self.why = cited, problem, fix, why

    def render(self):
        mark = "✖" if self.level == "error" else "⚠"
        return (f"{mark} {self.path}:{self.line} — `{self.cited}` — {self.problem}\n"
                f"  Why this matters: {self.why}\n"
                f"  Fix: {self.fix}")


def _git(root: Path, *args, stdin=None):
    """Run a git command under root. None if git is missing or errored."""
    try:
        proc = subprocess.run(["git", "-C", str(root), *args], input=stdin,
                              capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc


def git_ignored(root: Path, paths):
    """Subset of paths that git ignores under root.

    Empty when git is missing, when root is not inside a work tree, or when
    root *is itself* ignored by an enclosing work tree. That last case is the
    one worth spelling out: git walks upward, so checking a directory that is
    not its own repo silently answers from whatever repository encloses it. If
    that repository ignores the directory (a gitignored workspace, a vendored
    copy, a scratch checkout), every path under it comes back ignored and the
    filter would discard the entire doc set — reporting "no agent docs found"
    for a tree full of them. Ignoring is only meaningful relative to the repo
    the docs actually live in, so we skip filtering rather than trust it.
    """
    if not paths:
        return set()
    self_check = _git(root, "check-ignore", "--quiet", ".")
    if self_check is None or self_check.returncode not in (0, 1):
        return set()  # not a work tree (or git failed) — no filtering
    if self_check.returncode == 0:
        return set()  # root itself is ignored — the filter would eat everything
    rels = [p.relative_to(root).as_posix() for p in paths]
    proc = _git(root, "check-ignore", "--stdin", "-z", stdin="\0".join(rels))
    if proc is None or proc.returncode not in (0, 1):  # 0: some, 1: none
        return set()
    return {root / r for r in proc.stdout.split("\0") if r}


def candidate_docs(root: Path):
    """Every agent doc under root before --exclude and gitignore filtering.

    Kept separate from discover_docs so the caller can tell "this repo has no
    agent docs" apart from "filtering removed all of them" — the second is a
    misconfiguration that must not be reported as a clean run.
    """
    docs = []
    for pattern in ("AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "GEMINI.md",
                    "**/AGENTS.md", "**/CLAUDE.md",
                    ".github/copilot-instructions.md", ".claude/rules/*.md",
                    "docs/**/*.md"):
        for p in root.glob(pattern):
            # Match build dirs against the path *below* root only: p.parts
            # covers the absolute path, so a repo checked out under /tmp, or
            # any directory named build/out/target/..., would otherwise have
            # every one of its docs skipped and report a clean run.
            rel = p.relative_to(root)
            if p.is_file() and not any(part in BUILD_DIRS or part == ".git"
                                       for part in rel.parts):
                docs.append(p)
    return sorted(set(docs))


def discover_docs_detailed(root: Path, excludes=()):
    """(docs, n_excluded, n_gitignored) — the two filters counted separately.

    The caller needs them apart because they fail differently: an --exclude
    glob is the user's own explicit instruction, while gitignore filtering is
    invisible and can silently swallow every doc in the tree.
    """
    candidates = candidate_docs(root)
    kept = candidates
    if excludes:
        kept = [p for p in kept
                if not any(fnmatch.fnmatch(p.relative_to(root).as_posix(), pat)
                           for pat in excludes)]
    ignored = git_ignored(root, kept)
    docs = [p for p in kept if p not in ignored]
    return docs, len(candidates) - len(kept), len(ignored)


def discover_docs(root: Path, excludes=()):
    return discover_docs_detailed(root, excludes)[0]


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


def split_workspace(head, rest):
    """Strip workspace-targeting arguments from an npm/yarn/pnpm invocation.

    Returns (remaining_args, workspace); workspace is None when the command is
    not workspace-scoped. yarn's form is positional (`yarn workspace ws …`);
    npm and pnpm use flags. Only the first workspace value is kept, and the
    run-in-every-workspace flags map to "*", which the caller cannot resolve
    and therefore skips — both conservative choices.
    """
    if head == "yarn" and rest[:1] == ["workspace"] and len(rest) >= 3:
        return rest[2:], rest[1]
    flags = {"npm": ("-w", "--workspace"), "pnpm": ("-F", "--filter")}.get(head, ())
    out, ws, i = [], None, 0
    while i < len(rest):
        tok = rest[i]
        flag = next((f for f in flags if tok == f or tok.startswith(f + "=")), None)
        if head == "npm" and tok in ("--workspaces", "-ws"):
            ws = ws or "*"
        elif flag is None:
            out.append(tok)
        elif "=" in tok:
            ws = ws or tok.split("=", 1)[1]
        elif i + 1 < len(rest):
            ws = ws or rest[i + 1]
            i += 1
        i += 1
    return out, ws


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


CROSS_REPO = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*):([A-Za-z0-9._/#-]+)$")


def split_cross_repo(token: str):
    """(repo, path) when token is a `repo:path` cross-repo reference, else None.

    The colon form is the explicit idiom for citing a file in a sibling
    checkout: a sibling path written plainly is indistinguishable from a local
    one — it fails the local check, or worse, a same-named local file makes it
    pass while meaning the wrong file. Only tokens whose tail looks like a
    file reference qualify, so `12:30`, `key:value`, URI schemes, and Windows
    drive paths stay out.
    """
    m = CROSS_REPO.match(token)
    if not m:
        return None
    repo, path = m.groups()
    if path.startswith(("/", "./", "-")) or ".." in path:
        return None
    tail = path.rstrip("/").split("#")[0].split("/")[-1]
    ext = tail.rsplit(".", 1)[-1] if "." in tail else ""
    if not (path.endswith("/") or tail in KNOWN_FILES
            or ext.lower() in KNOWN_EXTS):
        return None
    return repo, path


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
        self.skipped = []  # (rel, lineno, token, reason) — seen, not judged
        self.checked = 0
        self._adr_index = None
        self._pkg_index = None

    def note_skip(self, rel, lineno, token, reason):
        """Record a token the matcher saw but deliberately did not judge.

        Silent skips are the coverage gap F-class: a doc author reads a clean
        run as "everything cited was checked" while the checker never judged
        the token at all. --verbose surfaces this list.
        """
        self.skipped.append((rel, lineno, token, reason))

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
        anchors = collect_anchors(lines, fm_end)

        in_fence, fence_lang, prev_continued = False, "", False
        for lineno, line in enumerate(lines, 1):
            if lineno <= fm_end:
                continue
            # Prose pointers are judged everywhere, fenced code included — the
            # observed failure mode is a dead pointer inside a command comment.
            self.check_prose_pointers(line, rel, lineno, lines)
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
            self.check_generalizations(line, rel, lineno, doc_dir)
            for m in INLINE_CODE.finditer(line):
                span = m.group(1).strip()
                if " " in span:
                    self.check_command_line(span, rel, lineno, doc_dir, npm, make, just,
                                            which_check=False)
                elif looks_like_path(span) or split_cross_repo(span):
                    self.check_path(span, rel, lineno, doc_dir)
            for m in MD_LINK.finditer(line):
                target = m.group(1)
                if target.startswith("#"):
                    self.check_anchor(target, rel, lineno, anchors)
                elif (not target.startswith(("http", "mailto:", "/"))
                        and not SKIP_CHARS & set(target)):
                    xr = split_cross_repo(target)
                    if xr:
                        self.check_cross_repo(xr, target, rel, lineno)
                        continue
                    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
                        continue  # URI scheme (tel:, vscode:, …), not a path
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
        for key in ("depends-on", "discovered-from", "relates-to"):
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

    def workspace_scripts(self, ws, doc_dir):
        """Scripts of the named workspace — a directory path or a package
        name. None when the workspace cannot be resolved; conservatively, an
        unresolved workspace suppresses the script check rather than judging
        it against the wrong manifest."""
        ws = ws.rstrip("./")  # pnpm's include-dependencies suffix (`ws...`)
        if not ws or SKIP_CHARS & set(ws) or ws.startswith("!"):
            return None
        for base in (self.root, doc_dir):
            pkg = base / ws / "package.json"
            if pkg.is_file():
                try:
                    return json.loads(pkg.read_text()).get("scripts", {})
                except (json.JSONDecodeError, OSError):
                    return None
        return self.package_index().get(ws)

    def workspace_exists(self, ws, doc_dir):
        """Whether ws names a package in this repo — by directory or by name.
        Distinct from workspace_scripts returning None: a package.json that
        exists but fails to parse is a real workspace with unknowable
        scripts, not a dead reference."""
        ws = ws.rstrip("./")
        return (any((base / ws / "package.json").is_file()
                    for base in (self.root, doc_dir))
                or ws in self.package_index())

    def binary_available(self, name, ws, doc_dir):
        """Whether a node binary of this name is findable — hoisted or
        workspace-local node_modules/.bin, or PATH. Absence is weak evidence
        (nothing may be installed here), which is why the caller warns rather
        than fails on it."""
        for base in (self.root, doc_dir):
            for d in (base / "node_modules" / ".bin",
                      base / ws.rstrip("./") / "node_modules" / ".bin"):
                if (d / name).exists():
                    return True
        return shutil.which(name) is not None

    def package_index(self):
        """Package name → scripts for every package.json under the repo root
        (build dirs and .git pruned during the walk, so node_modules is never
        descended into) — resolves workspaces named by package name."""
        if self._pkg_index is None:
            self._pkg_index = {}
            for dirpath, dirnames, filenames in os.walk(self.root):
                dirnames[:] = [d for d in dirnames
                               if d not in BUILD_DIRS and d != ".git"]
                if "package.json" not in filenames:
                    continue
                try:
                    data = json.loads(
                        (Path(dirpath) / "package.json").read_text())
                except (json.JSONDecodeError, OSError):
                    continue
                name = data.get("name") if isinstance(data, dict) else None
                if name:
                    self._pkg_index.setdefault(name, data.get("scripts", {}))
        return self._pkg_index

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

    def check_anchor(self, target, rel, lineno, anchors):
        anchor = target[1:].lower()
        if not anchor or SKIP_CHARS & set(anchor):
            return
        self.checked += 1
        # GitHub dedupes repeated headings with -N suffixes; accept those too.
        if anchor in anchors or re.sub(r"-\d+$", "", anchor) in anchors:
            return
        self.findings.append(Finding(
            "error", rel, lineno, target,
            f"no heading in this document matches this anchor"
            f"{suggest(anchor, anchors)}.",
            "fix the anchor, add the missing section, or drop the link.",
            WHY_DEAD_POINTER))

    def check_prose_pointers(self, line, rel, lineno, lines):
        for m in PROSE_POINTER.finditer(line):
            words = significant_words(m.group(1))
            if not words:
                continue  # only form/position words — nothing checkable
            direction = m.group(2).lower()
            region = lines[lineno:] if direction == "below" else lines[:lineno - 1]
            self.checked += 1
            stems = {word_stem(w) for w in WORD.findall("\n".join(region).lower())}
            if any(word_stem(w) in stems for w in words):
                continue
            self.findings.append(Finding(
                "error", rel, lineno, m.group(0),
                f"nothing {direction} this line mentions "
                + " or ".join(f'"{w}"' for w in words)
                + " — the pointer references content this document does not "
                  "contain.",
                "add the referenced content, point at where it actually "
                "lives, or drop the pointer.",
                WHY_DEAD_POINTER))

    def check_generalizations(self, line, rel, lineno, doc_dir):
        for sentence in SENTENCE_SPLIT.split(line):
            m = GENERALIZATION.search(sentence)
            if not m:
                continue
            # The quantifier scopes over what follows it: a directory named
            # *before* it is the subject being described ("`changes/` — one
            # fragment per user-facing change"), not the set being claimed
            # about, so only later citations count.
            dirs = self.cited_dirs(sentence[m.start():], doc_dir)
            if not dirs:
                continue
            self.checked += 1
            self.findings.append(Finding(
                "warning", rel, lineno, m.group(0).strip().replace("`", ""),
                f"this generalizes over the contents of `{dirs[0]}` — a claim "
                f"nothing here can decide, and the one self-review reliably "
                f"waves through because it just wrote it.",
                f"enumerate `{dirs[0]}` this session and keep the sentence only "
                f"if it holds for every entry; otherwise drop the quantifier and "
                f"name what you actually verified, or restate it as a rule the "
                f"repo enforces.",
                WHY_UNVERIFIED_CLAIM))

    def cited_dirs(self, sentence, doc_dir):
        """Backtick-quoted tokens in this sentence that name a directory —
        either explicitly (trailing '/') or by resolving to one in the repo."""
        found = []
        for m in INLINE_CODE.finditer(sentence):
            tok = m.group(1).strip()
            if (not tok or " " in tok or SKIP_CHARS & set(tok)
                    or tok.startswith(("/", "~", "http"))):
                continue
            if (tok.endswith("/") or (doc_dir / tok).is_dir()
                    or (self.root / tok).is_dir()):
                found.append(tok)
        return found

    def check_path(self, token, rel, lineno, doc_dir):
        xr = split_cross_repo(token)
        if xr:
            self.check_cross_repo(xr, token, rel, lineno)
            return
        if "/" in token and token.lstrip("./").split("/")[0] in BUILD_DIRS:
            self.note_skip(rel, lineno, token,
                           "under a build/output directory, which may "
                           "legitimately not exist — not judged")
            return
        # Slash tokens are only judged when their first segment is a real
        # directory (else `application/json` and friends false-positive) —
        # except .md references, which are unambiguous doc cross-links.
        if ("/" in token and not token.endswith(".md")
                and not first_segment_anchored(token, self.root, doc_dir)):
            seg = token.lstrip("./").split("/")[0]
            self.note_skip(rel, lineno, token,
                           f'first segment "{seg}" is not a directory next '
                           f"to this doc or at the repo root, so this may "
                           f"not be a repo path — not judged; if it is one, "
                           f"cite it relative to this doc or the root")
            return
        self.checked += 1
        if not path_exists(token, self.root, doc_dir):
            self.findings.append(Finding(
                "error", rel, lineno, token, "this path does not exist in the repo.",
                "correct the path, restore the file, or remove the stale reference."))

    def check_cross_repo(self, xr, token, rel, lineno):
        """Judge a `repo:path` reference against a sibling checkout ../repo.

        Without the sibling checked out there is nothing to judge against, so
        the token is skipped (visible under --verbose) rather than failed —
        the explicit form has already done its other job of never being
        mistaken for a local path.
        """
        repo, path = xr
        sibling = self.root.parent / repo
        if not sibling.is_dir():
            self.note_skip(rel, lineno, token,
                           f'cross-repo reference — no sibling checkout "../'
                           f'{repo}" to judge it against')
            return
        self.checked += 1
        clean = path.rstrip("/").split("#")[0]
        if not (sibling / clean).exists():
            self.findings.append(Finding(
                "error", rel, lineno, token,
                f'the sibling checkout of "{repo}" has no "{clean}".',
                "correct the path, or update the sibling checkout if it is "
                "stale — cross-repo references are judged whenever the named "
                "repo is checked out next to this one."))

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
            self.check_runner(tokens, rel, lineno, doc_dir, npm, make, just)
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

    def check_runner(self, tokens, rel, lineno, doc_dir, npm, make, just):
        head, rest = tokens[0], tokens[1:]
        def fail(cited, problem, fix):
            self.findings.append(Finding("error", rel, lineno, cited, problem, fix))

        if head in ("npm", "yarn", "pnpm"):
            rest, ws = split_workspace(head, rest)
            if ws is not None:
                npm = self.workspace_scripts(ws, doc_dir)
                if npm is None:
                    if ws == "*" or SKIP_CHARS & set(ws) or ws.startswith("!"):
                        return  # placeholder / every-workspace — nothing to judge
                    if head == "yarn" and not self.workspace_exists(ws, doc_dir):
                        # yarn's form is positional and unambiguous: the value
                        # IS a workspace name, so one that matches no package
                        # is a dead reference, not an unparseable filter.
                        self.checked += 1
                        fail(f"yarn workspace {ws}",
                             f'no workspace named "{ws}" exists in this repo'
                             f"{suggest(ws, self.package_index())}.",
                             "correct the workspace name, or add the package "
                             "the doc refers to.")
                    else:
                        self.note_skip(rel, lineno, f"{head} … {ws}",
                                       f'workspace "{ws}" could not be '
                                       f"resolved to a package.json — the "
                                       f"script was not judged")
                    return
            bare = False
            script = None
            if rest[:1] == ["run"] and len(rest) > 1:
                script = rest[1]
            elif rest[:1] in (["test"], ["start"]):
                script = rest[0]
            elif (head == "yarn" and ws is not None and rest
                  and not rest[0].startswith("-")
                  and rest[0] not in YARN_COMMANDS):
                # yarn allows omitting `run`: `yarn workspace ws build`. The
                # token may name a script or an installed binary — scripts are
                # judged here, unknown names fall back to a binary lookup.
                script, bare = rest[0], True
            if "--if-present" in rest:
                script = None  # missing script is explicitly tolerated
            if script and npm is not None:
                self.checked += 1
                if script in npm:
                    pass
                elif bare:
                    if not self.binary_available(script, ws, doc_dir):
                        self.findings.append(Finding(
                            "warning", rel, lineno,
                            f"yarn workspace {ws} {script}",
                            f'workspace "{ws}"\'s package.json has no script '
                            f'"{script}"{suggest(script, npm)}, and no binary '
                            f"of that name is findable (node_modules/.bin, "
                            f"PATH).",
                            "if this names a script, correct it; if it names "
                            "a binary this environment merely lacks, ignore — "
                            "or use the explicit `run` form, which is judged "
                            "strictly."))
                else:
                    where = (f'workspace "{ws}"\'s package.json' if ws
                             else "package.json")
                    fail(f"{head} {'run ' if rest[:1] == ['run'] else ''}{script}",
                         f'{where} has no script "{script}"{suggest(script, npm)}.',
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
                    help="treat warnings (PATH lookups, missing Makefile, "
                         "unverified generalizations) as errors")
    ap.add_argument("--verbose", "-v", action="store_true",
                    help="also list tokens that were seen but not judged "
                         "(unanchored paths, build-dir paths, unresolvable "
                         "workspaces, cross-repo references without a sibling "
                         "checkout) — the coverage boundary a clean run says "
                         "nothing about")
    ap.add_argument("--exclude", action="append", default=[], metavar="GLOB",
                    help="skip discovered docs whose repo-relative path matches "
                         "this glob (repeatable; * also crosses '/'); files "
                         "named explicitly are never excluded")
    ap.add_argument("--require-docs", action="store_true",
                    help="fail when no agent docs are found or none survive "
                         "filtering — for CI gates, where losing the docs must "
                         "not turn the gate green")
    args = ap.parse_args()

    paths = [Path(p).resolve() for p in (args.paths or ["."])]
    n_excluded = n_gitignored = 0
    if len(paths) == 1 and paths[0].is_dir():
        root = paths[0]
        docs, n_excluded, n_gitignored = discover_docs_detailed(root, args.exclude)
    else:
        files = [p for p in paths if p.is_file()]
        if len(files) != len(paths):
            missing = [str(p) for p in paths if not p.is_file()]
            print(f"error: not a file: {', '.join(missing)}", file=sys.stderr)
            return 2
        root, docs = Path.cwd().resolve(), files

    if not docs:
        if n_gitignored:
            # Docs exist and gitignore filtering — which the user never asked
            # for and cannot see — removed every one. Exiting 0 would green-light
            # a repo the check cannot read, so this is an error.
            print(f"✖ {root} — {n_gitignored} agent doc(s) found but all were "
                  f"discarded as gitignored, so nothing was checked.\n"
                  f"  Why this matters: a docs gate that discovers nothing still "
                  f"exits 0, so it reports success forever while the docs it "
                  f"should guard drift unchecked.\n"
                  f"  Fix: check whether an enclosing repository's .gitignore "
                  f"covers this directory — name the docs explicitly to bypass "
                  f"discovery: check_docs.py AGENTS.md CLAUDE.md")
            print("Result: FAIL — nothing was checked.")
            return 1
        if n_excluded:
            # The user's own --exclude globs matched everything. Deliberate, so
            # not an error by default, but still worth saying out loud.
            print(f"⚠ {root} — {n_excluded} agent doc(s) found but all matched "
                  f"--exclude, so nothing was checked.\n"
                  f"  Why this matters: the run passes without having checked "
                  f"anything, which reads as a clean gate.\n"
                  f"  Fix: narrow the --exclude globs if that was not intended.")
            if args.strict or args.require_docs:
                flag = "--require-docs" if args.require_docs else "--strict"
                print(f"Result: FAIL — nothing was checked ({flag}).")
                return 1
            print("Result: OK — nothing was checked.")
            return 0
        if args.require_docs:
            print(f"✖ {root} — no agent docs found, and --require-docs is set.\n"
                  f"  Why this matters: this gate exists because the repo is "
                  f"supposed to have agent docs; without --require-docs, "
                  f"deleting or renaming the last one would return the gate to "
                  f"'nothing to check' and report success forever.\n"
                  f"  Fix: restore the missing docs (AGENTS.md and friends), or "
                  f"drop --require-docs if this repo genuinely keeps none.")
            print("Result: FAIL — nothing was checked.")
            return 1
        print(f"check_docs: no agent docs found under {root} — nothing to check.")
        return 0

    checker = Checker(root)
    for doc in docs:
        checker.check_file(doc)

    errors = [f for f in checker.findings if f.level == "error"]
    warnings = [f for f in checker.findings if f.level == "warning"]
    for f in errors + warnings:
        print(f.render(), end="\n\n")
    if args.verbose and checker.skipped:
        print(f"Not judged — {len(checker.skipped)} token(s) the matcher saw "
              f"but deliberately did not check:")
        for rel, lineno, token, reason in checker.skipped:
            print(f"  ~ {rel}:{lineno} — `{token}` — {reason}")
        print()
    summary = (f"check_docs: {len(docs)} doc(s), {checker.checked} "
               f"reference(s) checked — {len(errors)} error(s), "
               f"{len(warnings)} warning(s)")
    if checker.skipped:
        summary += f", {len(checker.skipped)} token(s) not judged"
        if not args.verbose:
            summary += " (--verbose lists them)"
    print(summary + ".")
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
