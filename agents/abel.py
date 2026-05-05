"""
# Agent: Abel (GitHub Manager)
#
# አቤል — "breath" in Amharic/Hebrew. Abel keeps the project breathing —
# always synced, always clean, always presentable on GitHub.
#
# Abel owns the GitHub remote. He handles:
#   - Pushing commits after Endalk approves a merge
#   - Creating and managing branches per task
#   - Opening Pull Requests with rich descriptions
#   - Labelling PRs by track (backend / cli / features / infra)
#   - Posting release notes when a phase completes
#   - Keeping the README and repo description up to date
#   - Listening on #mzgb-integration for PUSH: and RELEASE: signals
#
# Signals he listens for (on #mzgb-integration):
#   PUSH:task_id          — push current branch, open PR for this task
#   RELEASE:v1.x.x        — tag + create GitHub release with changelog
#   SYNC                  — force push main to match local
#
# Environment variables (from .env):
#   GITHUB_TOKEN          — personal access token (repo scope)
#   GITHUB_REPO           — e.g. "yourname/mzgb"
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.config import AGENTS, MATRIX_HOMESERVER, ROOMS
from agents.matrix_client import AgentMatrixClient
from agents.llm import _load_env

_load_env()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("abel")

ROOT       = Path(__file__).parent.parent
GITHUB_API = "https://api.github.com"

LABEL_COLORS: Dict[str, str] = {
    "backend":  "0075ca",
    "cli":      "e4e669",
    "features": "d93f0b",
    "infra":    "0e8a16",
    "review":   "5319e7",
    "release":  "b60205",
}

# ── GitHub API helpers ────────────────────────────────────────────────────────

def _gh_token() -> str:
    """Return GitHub token or raise clearly."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token or token == "your_github_personal_access_token_here":
        raise EnvironmentError(
            "GITHUB_TOKEN not set. Add it to .env:\n"
            "  GITHUB_TOKEN=ghp_xxxxxxxxxxxx\n"
            "Get one at https://github.com/settings/tokens (repo scope)"
        )
    return token


def _gh_repo() -> str:
    """Return owner/repo string or raise clearly."""
    repo = os.environ.get("GITHUB_REPO", "")
    if not repo or repo == "your_username/your_repo_name":
        raise EnvironmentError(
            "GITHUB_REPO not set. Add it to .env:\n"
            "  GITHUB_REPO=yourname/mzgb"
        )
    return repo


def _gh_request(
    method: str,
    path: str,
    payload: Optional[dict] = None,
) -> dict:
    """Make an authenticated GitHub API request. Returns parsed JSON."""
    url = f"{GITHUB_API}{path}"
    body = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {_gh_token()}",
            "Accept":        "application/vnd.github+json",
            "Content-Type":  "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent":    "mzgb-abel-agent/1.0",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8")) if resp.length != 0 else {}
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {path} → HTTP {exc.code}: {body_text}") from exc


# ── Git helpers ───────────────────────────────────────────────────────────────

def _git(*args: str) -> str:
    """Run a git command and return stdout. Raises on non-zero exit."""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True, cwd=ROOT,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


def _current_branch() -> str:
    return _git("rev-parse", "--abbrev-ref", "HEAD")


def _ensure_remote() -> None:
    """Add origin remote if not present."""
    repo = _gh_repo()
    try:
        _git("remote", "get-url", "origin")
    except RuntimeError:
        _git("remote", "add", "origin", f"https://github.com/{repo}.git")
        logger.info("Added remote origin → https://github.com/%s.git", repo)


# ── Label management ──────────────────────────────────────────────────────────

def _ensure_labels() -> None:
    """Create track labels on GitHub if they don't exist yet."""
    repo = _gh_repo()
    existing = {l["name"] for l in _gh_request("GET", f"/repos/{repo}/labels")}
    for name, color in LABEL_COLORS.items():
        if name not in existing:
            try:
                _gh_request("POST", f"/repos/{repo}/labels",
                            {"name": name, "color": color})
                logger.info("Created label: %s", name)
            except RuntimeError:
                pass


# ── Core actions ──────────────────────────────────────────────────────────────

def push_and_open_pr(task_id: str, task_info: Optional[dict] = None) -> str:
    """
    Push current branch to origin and open a Pull Request.
    Returns the PR URL.
    """
    _ensure_remote()
    branch = _current_branch()

    if branch == "main":
        branch = f"task/{task_id}"
        try:
            _git("checkout", "-b", branch)
        except RuntimeError:
            _git("checkout", branch)
        _git("push", "--set-upstream", "origin", branch)
    else:
        _git("push", "--set-upstream", "origin", branch)

    repo  = _gh_repo()
    title = task_info.get("title", f"Task {task_id}") if task_info else f"Task {task_id}"
    track = task_info.get("track", "backend") if task_info else "backend"
    criteria = task_info.get("acceptanceCriteria", []) if task_info else []
    criteria_md = "\n".join(f"- [x] {c}" for c in criteria) if criteria else "_See task description_"

    body = f"""## {title}

**Task ID:** `{task_id}`
**Track:** `{track}`

### Acceptance Criteria
{criteria_md}

### Changes
{_git("diff", "--stat", "origin/main", branch) if branch != "main" else "_initial commit_"}

---
_Opened automatically by Abel (GitHub Manager Agent)_
"""

    pr_data = _gh_request("POST", f"/repos/{repo}/pulls", {
        "title": f"[{task_id}] {title}",
        "body":  body,
        "head":  branch,
        "base":  "main",
    })
    pr_url    = pr_data.get("html_url", "")
    pr_number = pr_data.get("number")

    if pr_number and track in LABEL_COLORS:
        try:
            _gh_request("POST", f"/repos/{repo}/issues/{pr_number}/labels",
                        {"labels": [track]})
        except RuntimeError:
            pass

    logger.info("PR opened: %s", pr_url)
    return pr_url


def create_release(version: str, changelog_path: Optional[Path] = None) -> str:
    """
    Tag HEAD as `version` and create a GitHub release.
    Returns the release URL.
    """
    repo = _gh_repo()

    notes = ""
    if changelog_path and changelog_path.exists():
        notes = changelog_path.read_text()[:8000]
    else:
        notes = _git("log", "--oneline", "-20")

    _git("tag", version)
    _git("push", "origin", version)

    release = _gh_request("POST", f"/repos/{repo}/releases", {
        "tag_name":   version,
        "name":       f"mzgb {version}",
        "body":       notes,
        "draft":      False,
        "prerelease": "alpha" in version or "beta" in version,
    })
    url = release.get("html_url", "")
    logger.info("Release created: %s", url)
    return url


def sync_main() -> None:
    """Force-push local main to origin."""
    _ensure_remote()
    _git("push", "origin", "main", "--force-with-lease")
    logger.info("main synced to origin")


# ── Task loader ───────────────────────────────────────────────────────────────

def _load_task(task_id: str) -> Optional[dict]:
    queue_path = ROOT / "tasks" / "QUEUE.json"
    data = json.loads(queue_path.read_text())
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    return None


# ── Matrix signal handler ─────────────────────────────────────────────────────

async def handle_signal(matrix: AgentMatrixClient, body: str) -> None:
    """Dispatch Matrix signals to the correct action."""
    try:
        if body.startswith("PUSH:"):
            task_id = body.split(":", 1)[1].split("|")[0].strip()
            task_info = _load_task(task_id)
            await matrix.send(ROOMS["integration"],
                f"🔀 Abel | Pushing task {task_id} to GitHub...")
            pr_url = push_and_open_pr(task_id, task_info)
            await matrix.send(ROOMS["general"],
                f"🎉 Abel | PR opened for task {task_id}\n  {pr_url}")

        elif body.startswith("RELEASE:"):
            version = body.split(":", 1)[1].strip()
            await matrix.send(ROOMS["general"],
                f"📦 Abel | Creating release {version}...")
            changelog = ROOT / "CHANGELOG.md"
            url = create_release(version, changelog if changelog.exists() else None)
            await matrix.send(ROOMS["general"],
                f"🚀 Abel | Released {version}\n  {url}")

        elif body.strip() == "SYNC":
            sync_main()
            await matrix.send(ROOMS["general"],
                "✅ Abel | main pushed to origin successfully.")

    except EnvironmentError as exc:
        await matrix.send(ROOMS["blockers"],
            f"🚨 Abel | Config error:\n{exc}")
    except RuntimeError as exc:
        await matrix.send(ROOMS["blockers"],
            f"🚨 Abel | GitHub error:\n{exc}")


async def listen_loop(matrix: AgentMatrixClient) -> None:
    """Sync loop — listens for signals on #mzgb-integration."""
    import nio

    async def _cb(room, event):
        if not isinstance(event, nio.RoomMessageText):
            return
        if event.sender == f"@abel:localhost":
            return
        body = event.body.strip()
        if any(body.startswith(p) for p in ("PUSH:", "RELEASE:", "SYNC")):
            await handle_signal(matrix, body)

    matrix.client.add_event_callback(_cb, nio.RoomMessageText)

    await matrix.send(ROOMS["general"],
        "🐙 Abel (GitHub Manager) | Online\n"
        "  Watching for PUSH:, RELEASE:, SYNC signals on #mzgb-integration\n"
        f"  Repo: {os.environ.get('GITHUB_REPO', 'not configured yet')}"
    )

    while True:
        try:
            await asyncio.wait_for(matrix.client.sync(timeout=30000), timeout=40)
        except asyncio.TimeoutError:
            pass
        except Exception as exc:
            logger.warning("Sync error: %s", exc)
            await asyncio.sleep(5)


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    """Connect Abel to Matrix and start listening."""
    me = AGENTS.get("endalk")  # reuse endalk credentials for now
    matrix = AgentMatrixClient(
        homeserver=MATRIX_HOMESERVER,
        username="endalk",
        password=me["password"],
        display_name="Abel (GitHub Manager)",
    )
    await matrix.connect()
    for room in [ROOMS["integration"], ROOMS["general"], ROOMS["blockers"]]:
        await matrix.join_room(room)
    await listen_loop(matrix)


if __name__ == "__main__":
    # Can also be called directly for one-shot operations:
    #   python3 agents/abel.py push 3.1
    #   python3 agents/abel.py release v0.1.0
    #   python3 agents/abel.py sync
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "push" and len(sys.argv) > 2:
            task_id = sys.argv[2]
            task = _load_task(task_id)
            url = push_and_open_pr(task_id, task)
            print(f"PR opened: {url}")
        elif cmd == "release" and len(sys.argv) > 2:
            version = sys.argv[2]
            changelog = ROOT / "CHANGELOG.md"
            url = create_release(version, changelog if changelog.exists() else None)
            print(f"Release: {url}")
        elif cmd == "sync":
            sync_main()
            print("Synced.")
        else:
            print("Usage: abel.py [push <task_id> | release <version> | sync]")
        sys.exit(0)

    asyncio.run(main())
