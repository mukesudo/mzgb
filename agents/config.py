"""
Shared configuration for all LogSnap AI agents.
Homeserver and room settings live here.
"""

MATRIX_HOMESERVER = "http://localhost:8008"

# Matrix rooms — one per coordination channel
ROOMS = {
    "general":     "#logsnap-general:localhost",
    "backend":     "#logsnap-backend:localhost",
    "cli":         "#logsnap-cli:localhost",
    "features":    "#logsnap-features:localhost",
    "infra":       "#logsnap-infra:localhost",
    "integration": "#logsnap-integration:localhost",
    "blockers":    "#logsnap-blockers:localhost",
}

# Task file paths (relative to project root)
import pathlib
ROOT = pathlib.Path(__file__).parent.parent

TASK_FILES = {
    "backend":  ROOT / "tasks/backend.md",
    "cli":      ROOT / "tasks/cli.md",
    "features": ROOT / "tasks/features.md",
    "infra":    ROOT / "tasks/infra.md",
    "testing":  ROOT / "tasks/testing.md",
}

# Agent credentials — stored here for local dev only
# In production: load from environment variables or a secrets manager
AGENTS = {
    "biruk": {
        "username": "biruk",
        "password": "biruk-logsnap-dev",
        "display_name": "Biruk (Backend)",
        "track": "backend",
    },
    "liya": {
        "username": "liya",
        "password": "liya-logsnap-dev",
        "display_name": "Liya (CLI & Renderer)",
        "track": "cli",
    },
    "tigist": {
        "username": "tigist",
        "password": "tigist-logsnap-dev",
        "display_name": "Tigist (Features)",
        "track": "features",
    },
    "natnael": {
        "username": "natnael",
        "password": "natnael-logsnap-dev",
        "display_name": "Natnael (Infra & Testing)",
        "track": "infra",
    },
}
