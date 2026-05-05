"""
# Agent: Dawit (Senior Developer Reviewer)
#
# ዳዊት — "beloved" in Amharic/Hebrew. Dawit is the greybeard on the team.
# He has seen every anti-pattern twice and has strong opinions.
# He does not merge without a review. He does not approve without evidence.
#
# Triggered by: post-commit hook (via git hook or direct call)
# Arguments:   list of changed .py files (from git diff --name-only HEAD~1)
#
# What he does:
#   1. Loads the checklist from .windsurf/senior_review.yaml
#   2. Runs pylint on each changed file
#   3. Runs AST-based structural analysis (nesting, length, docstrings, type hints)
#   4. Produces a structured report with PASS / WARN / BLOCK verdicts
#   5. Posts the report to #mzgb-integration on Matrix
#   6. Exits non-zero if any BLOCK-level findings exist
#
# Usage (from post-commit hook):
#   python3 agents/dawit.py [file1.py file2.py ...]
#   python3 agents/dawit.py --staged        # review files staged in last commit
"""

import ast
import json
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

ROOT = Path(__file__).parent.parent
CHECKLIST_PATH = ROOT / ".windsurf" / "senior_review.yaml"

# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class Finding:
    """A single checklist violation found in a file."""
    rule_id: str
    severity: str          # error | warning | info
    file: str
    line: Optional[int]
    message: str
    context: Optional[str] = None


@dataclass
class ReviewReport:
    """Full review report for a commit."""
    commit: str
    files_reviewed: List[str] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)

    @property
    def errors(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "warning"]

    @property
    def infos(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "info"]

    @property
    def verdict(self) -> str:
        if self.errors:
            return "BLOCK"
        if self.warnings:
            return "WARN"
        return "APPROVE"


# ── Checklist loader ───────────────────────────────────────────────────────────

def load_checklist() -> dict:
    with open(CHECKLIST_PATH) as fh:
        return yaml.safe_load(fh)


# ── Pylint runner ──────────────────────────────────────────────────────────────

def run_pylint(filepath: str) -> List[Finding]:
    """Run pylint and parse JSON output into Findings."""
    result = subprocess.run(
        [
            sys.executable, "-m", "pylint",
            "--output-format=json",
            "--disable=all",
            "--enable=W0703,C0103,C0114,C0116,R0912,R0914,R0915",
            filepath,
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    findings = []
    try:
        messages = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return findings

    severity_map = {
        "error":      "error",
        "warning":    "warning",
        "convention": "warning",
        "refactor":   "warning",
        "fatal":      "error",
    }
    rule_map = {
        "W0703": "no-bare-except",
        "C0103": "no-single-letter-vars",
        "C0114": "module-docstring",
        "C0116": "public-methods-documented",
        "R0912": "max-complexity",
        "R0914": "max-function-length",
        "R0915": "max-function-length",
    }

    for msg in messages:
        rule_id = rule_map.get(msg.get("message-id", ""), msg.get("message-id", "pylint"))
        sev = severity_map.get(msg.get("type", "warning"), "warning")
        findings.append(Finding(
            rule_id=rule_id,
            severity=sev,
            file=filepath,
            line=msg.get("line"),
            message=msg.get("message", ""),
            context=msg.get("symbol"),
        ))
    return findings


# ── AST-based structural analysis ─────────────────────────────────────────────

def _indent_level(node: ast.AST) -> int:
    """Estimate max nesting depth inside a function body."""
    max_depth = [0]

    def _walk(node, depth):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.With,
                              ast.Try, ast.ExceptHandler)):
            depth += 1
            max_depth[0] = max(max_depth[0], depth)
        for child in ast.iter_child_nodes(node):
            _walk(child, depth)

    _walk(node, 0)
    return max_depth[0]


def run_ast_checks(filepath: str, thresholds: dict) -> List[Finding]:
    """Run structural AST checks against the checklist thresholds."""
    findings = []
    source = Path(filepath).read_text(encoding="utf-8", errors="replace")

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as exc:
        findings.append(Finding(
            rule_id="syntax-error",
            severity="error",
            file=filepath,
            line=exc.lineno,
            message=f"Syntax error: {exc.msg}",
        ))
        return findings

    source_lines = source.splitlines()
    default_fn_lines   = 40
    default_nesting    = 3
    default_cls_lines  = 200
    default_cls_methods = 10
    max_fn_lines   = thresholds.get("function_max_lines",      default_fn_lines)
    max_nesting    = thresholds.get("nesting_max",             default_nesting)
    max_cls_lines  = thresholds.get("class_max_lines",        default_cls_lines)
    max_cls_methods = thresholds.get("class_max_public_methods", default_cls_methods)

    # Module docstring
    if not (isinstance(tree.body[0], ast.Expr) and
            isinstance(tree.body[0].value, ast.Constant) and
            isinstance(tree.body[0].value.value, str)):
        findings.append(Finding(
            rule_id="module-docstring",
            severity="info",
            file=filepath,
            line=1,
            message="Module is missing a top-level docstring.",
        ))

    for node in ast.walk(tree):
        # Function checks
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            start = node.lineno
            end = node.end_lineno or start
            fn_lines = end - start + 1

            # Length
            if fn_lines > max_fn_lines:
                findings.append(Finding(
                    rule_id="max-function-length",
                    severity="warning",
                    file=filepath,
                    line=start,
                    message=f"Function `{name}` is {fn_lines} lines (max {max_fn_lines}).",
                ))

            # Nesting
            nesting = _indent_level(node)
            if nesting > max_nesting:
                findings.append(Finding(
                    rule_id="max-nesting",
                    severity="warning",
                    file=filepath,
                    line=start,
                    message=f"Function `{name}` has nesting depth {nesting} (max {max_nesting}).",
                ))

            # Public methods — docstring required
            if not name.startswith("_"):
                if not (node.body and isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)):
                    findings.append(Finding(
                        rule_id="public-methods-documented",
                        severity="warning",
                        file=filepath,
                        line=start,
                        message=f"Public function `{name}` has no docstring.",
                    ))

            # Type hints
            args = node.args
            all_args = args.args + args.posonlyargs + args.kwonlyargs
            missing_hints = [
                a.arg for a in all_args
                if a.arg != "self" and a.annotation is None
            ]
            if missing_hints or (not name.startswith("_") and node.returns is None):
                findings.append(Finding(
                    rule_id="type-hints-required",
                    severity="warning",
                    file=filepath,
                    line=start,
                    message=(
                        f"Function `{name}` missing type hints: "
                        f"args={missing_hints or 'ok'}, "
                        f"return={'missing' if node.returns is None else 'ok'}."
                    ),
                ))

            # Silent fallbacks: `or 0`, `or None`, `or ""`
            # dawit.py is exempt — it contains these strings as detection patterns
            if Path(filepath).name != "dawit.py":
                fn_source = "\n".join(source_lines[start - 1:end])
                _fallback_patterns = [
                    (" or 0",    "or 0"),
                    (" or None", "or None"),
                    (' or ""',   'or ""'),
                    (" or ''",   "or ''"),
                ]
                for _pat, _example in _fallback_patterns:
                    if _pat in fn_source:
                        findings.append(Finding(
                            rule_id="no-silent-fallback",
                            severity="error",
                            file=filepath,
                            line=start,
                            message=f"Silent fallback `{_example}` in `{name}`. Use explicit validation.",
                            context=fn_source[:120],
                        ))
                        break

        # Class checks
        if isinstance(node, ast.ClassDef):
            cls_start = node.lineno
            cls_end = node.end_lineno or cls_start
            cls_lines = cls_end - cls_start + 1
            public_methods = [
                n for n in ast.walk(node)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not n.name.startswith("_")
            ]
            if cls_lines > max_cls_lines:
                findings.append(Finding(
                    rule_id="no-god-class",
                    severity="warning",
                    file=filepath,
                    line=cls_start,
                    message=f"Class `{node.name}` is {cls_lines} lines (max {max_cls_lines}).",
                ))
            if len(public_methods) > max_cls_methods:
                findings.append(Finding(
                    rule_id="no-god-class",
                    severity="warning",
                    file=filepath,
                    line=cls_start,
                    message=(
                        f"Class `{node.name}` has {len(public_methods)} public methods "
                        f"(max {max_cls_methods})."
                    ),
                ))

    # Catchall filename check
    basename = Path(filepath).name
    catchall = {"functions.py", "helpers.py", "utils.py", "misc.py", "common.py"}
    if basename in catchall:
        findings.append(Finding(
            rule_id="no-catchall-files",
            severity="error",
            file=filepath,
            line=1,
            message=f"Catchall module `{basename}` detected. Split into focused modules.",
        ))

    return findings


# ── Report formatter ───────────────────────────────────────────────────────────

ICONS = {"error": "🚨", "warning": "⚠️ ", "info": "ℹ️ "}
SEV_ORDER = {"error": 0, "warning": 1, "info": 2}


def format_report(report: ReviewReport) -> str:
    verdict_icon = {"BLOCK": "🔴 BLOCK", "WARN": "🟡 WARN", "APPROVE": "🟢 APPROVE"}[report.verdict]
    lines = [
        f"╔══ Dawit (Senior Review) ══ {verdict_icon} ══╗",
        f"  Commit : {report.commit[:12]}",
        f"  Files  : {len(report.files_reviewed)}  |  "
        f"Errors: {len(report.errors)}  Warnings: {len(report.warnings)}  Info: {len(report.infos)}",
        "",
    ]

    if not report.findings:
        lines.append("  ✅ No issues found. Clean commit.")
    else:
        # Group by file
        by_file: dict = {}
        for f in sorted(report.findings, key=lambda x: SEV_ORDER[x.severity]):
            by_file.setdefault(f.file, []).append(f)

        for filepath, file_findings in by_file.items():
            rel = str(Path(filepath).relative_to(ROOT))
            lines.append(f"  📄 {rel}")
            for finding in file_findings:
                icon = ICONS[finding.severity]
                loc = f"L{finding.line}" if finding.line else "   "
                lines.append(f"    {icon} [{finding.rule_id}] {loc} — {finding.message}")
            lines.append("")

    if report.verdict == "BLOCK":
        lines += [
            "  ─────────────────────────────────────────",
            "  🚫 MERGE BLOCKED — fix errors above before merging.",
        ]
    elif report.verdict == "WARN":
        lines += [
            "  ─────────────────────────────────────────",
            "  ⚠️  Warnings found. Fix recommended before merge.",
            "  To override: git commit --no-verify (use sparingly).",
        ]
    else:
        lines.append("  ✅ APPROVED for merge.")

    lines.append("╚══════════════════════════════════════════╝")
    return "\n".join(lines)


# ── Matrix poster ──────────────────────────────────────────────────────────────

def post_to_matrix(report_text: str) -> None:
    """Post report to #mzgb-integration. Fails silently if Matrix is down."""
    try:
        import asyncio
        import time

        import aiohttp

        sys.path.insert(0, str(ROOT))
        from agents.config import AGENTS, MATRIX_HOMESERVER

        creds = AGENTS.get("endalk") or list(AGENTS.values())[0]

        async def _post():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{MATRIX_HOMESERVER}/_matrix/client/v3/login",
                    json={
                        "type": "m.login.password",
                        "identifier": {"type": "m.id.user", "user": creds["username"]},
                        "password": creds["password"],
                    },
                ) as resp:
                    data = await resp.json()
                    token = data.get("access_token")
                    if not token:
                        return

                # Resolve room alias to ID
                async with session.get(
                    f"{MATRIX_HOMESERVER}/_matrix/client/v3/directory/room/%23mzgb-integration%3Alocalhost",
                    headers={"Authorization": f"Bearer {token}"},
                ) as resp:
                    room_data = await resp.json()
                    room_id = room_data.get("room_id")
                    if not room_id:
                        return

                txn_id = int(time.time() * 1000)
                async with session.put(
                    f"{MATRIX_HOMESERVER}/_matrix/client/v3/rooms/{room_id}"
                    f"/send/m.room.message/{txn_id}",
                    json={"msgtype": "m.text", "body": report_text},
                    headers={"Authorization": f"Bearer {token}"},
                ):
                    pass

        asyncio.run(_post())
    except Exception:
        pass  # Matrix posting is best-effort; never block the commit


# ── Main entry point ───────────────────────────────────────────────────────────

def get_changed_files() -> List[str]:
    """Get Python files changed in the last commit."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        capture_output=True, text=True, cwd=ROOT,
    )
    files = []
    for line in result.stdout.splitlines():
        p = ROOT / line.strip()
        if p.suffix == ".py" and p.exists():
            files.append(str(p))
    return files


def get_commit_hash() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True, cwd=ROOT,
    )
    return result.stdout.strip()


def review(files: List[str]) -> ReviewReport:
    checklist = load_checklist()
    thresholds = checklist.get("thresholds", {})
    commit = get_commit_hash()

    report = ReviewReport(commit=commit, files_reviewed=files)

    for filepath in files:
        report.findings.extend(run_pylint(filepath))
        report.findings.extend(run_ast_checks(filepath, thresholds))

    # Deduplicate (same rule + file + line)
    seen = set()
    deduped = []
    for f in report.findings:
        key = (f.rule_id, f.file, f.line)
        if key not in seen:
            seen.add(key)
            deduped.append(f)
    report.findings = deduped

    return report


def main() -> int:
    args = sys.argv[1:]

    if "--staged" in args or not args:
        files = get_changed_files()
    else:
        files = [str(ROOT / a) if not Path(a).is_absolute() else a for a in args]
        files = [f for f in files if Path(f).exists() and f.endswith(".py")]

    if not files:
        print("Dawit: no Python files to review.")
        return 0

    print(f"Dawit: reviewing {len(files)} file(s)...")
    report = review(files)
    output = format_report(report)

    print(output)
    post_to_matrix(output)

    if report.verdict == "BLOCK":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
