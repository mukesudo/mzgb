"""
bootstrap.py — One-time setup for the mzgb agent Matrix environment.

Run this ONCE after `docker compose up` to:
  1. Register all agent accounts on the Synapse homeserver
  2. Create all coordination rooms
  3. Invite all agents to all rooms
  4. Post a welcome message confirming the environment is ready

Usage:
    python3 agents/bootstrap.py
"""

import asyncio
import logging
import sys
from pathlib import Path

import aiohttp

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.config import AGENTS, MATRIX_HOMESERVER, ROOMS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("bootstrap")

REGISTRATION_SECRET = "mzgb-dev-secret-change-in-prod"


async def register_agent(session: aiohttp.ClientSession, username: str, password: str) -> bool:
    """Register a user account, retrying on rate-limit errors."""
    url = f"{MATRIX_HOMESERVER}/_matrix/client/v3/register"
    payload = {
        "username": username,
        "password": password,
        "auth": {"type": "m.login.dummy"},
    }
    for attempt in range(5):
        async with session.post(url, json=payload) as resp:
            body = await resp.json()
            if body.get("errcode") == "M_USER_IN_USE":
                logger.info("  [%s] Already registered — skipping", username)
                return True
            if resp.status == 200:
                logger.info("  [%s] Registered ✓", username)
                return True
            if body.get("errcode") == "M_LIMIT_EXCEEDED":
                wait = (body.get("retry_after_ms", 3000) / 1000) + 1
                logger.warning("  [%s] Rate limited — waiting %.1fs (attempt %d)", username, wait, attempt + 1)
                await asyncio.sleep(wait)
                continue
            logger.error("  [%s] Registration failed: %s", username, body)
            return False
    logger.error("  [%s] Registration failed after retries", username)
    return False


async def login_agent(session: aiohttp.ClientSession, username: str, password: str) -> str:
    """Login and return an access token, retrying on rate-limit errors."""
    url = f"{MATRIX_HOMESERVER}/_matrix/client/v3/login"
    payload = {
        "type": "m.login.password",
        "identifier": {"type": "m.id.user", "user": username},
        "password": password,
    }
    for attempt in range(10):
        async with session.post(url, json=payload) as resp:
            body = await resp.json()
            if body.get("errcode") == "M_LIMIT_EXCEEDED":
                wait = (body.get("retry_after_ms", 5000) / 1000) + 1
                logger.warning("  [%s] Rate limited on login — waiting %.1fs (attempt %d)", username, wait, attempt + 1)
                await asyncio.sleep(wait)
                continue
            token = body.get("access_token")
            if not token:
                raise RuntimeError(f"Login failed for {username}: {body}")
            logger.info("  [%s] Logged in ✓", username)
            return token
    raise RuntimeError(f"Login failed for {username} after retries — rate limit persists")


async def create_room(session: aiohttp.ClientSession, token: str, alias: str) -> str:
    """Create a room with a local alias. Returns room_id."""
    local_alias = alias.split(":")[0].lstrip("#")
    url = f"{MATRIX_HOMESERVER}/_matrix/client/v3/createRoom"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "room_alias_name": local_alias,
        "name": f"mzgb {local_alias.replace('mzgb-', '').title()}",
        "topic": f"mzgb agent coordination — {local_alias}",
        "preset": "public_chat",
        "visibility": "public",
    }
    async with session.post(url, json=payload, headers=headers) as resp:
        body = await resp.json()
        if body.get("errcode") == "M_ROOM_IN_USE":
            logger.info("  Room %s already exists — skipping", alias)
            # Resolve alias to room_id
            async with session.get(
                f"{MATRIX_HOMESERVER}/_matrix/client/v3/directory/room/{alias.replace('#', '%23')}",
                headers=headers
            ) as r2:
                d = await r2.json()
                return d.get("room_id", "")
        room_id = body.get("room_id", "")
        logger.info("  Room %s created: %s", alias, room_id)
        return room_id


async def set_room_public(session: aiohttp.ClientSession, token: str, room_id: str) -> None:
    """Ensure an existing room has join_rules=public so agents can join without invite."""
    url = f"{MATRIX_HOMESERVER}/_matrix/client/v3/rooms/{room_id}/state/m.room.join_rules"
    headers = {"Authorization": f"Bearer {token}"}
    async with session.put(url, json={"join_rule": "public"}, headers=headers) as resp:
        body = await resp.json()
        if resp.status != 200:
            logger.warning("  Could not set join_rules on %s: %s", room_id, body)


async def invite_to_room(session: aiohttp.ClientSession, token: str, room_id: str, user_id: str):
    url = f"{MATRIX_HOMESERVER}/_matrix/client/v3/rooms/{room_id}/invite"
    headers = {"Authorization": f"Bearer {token}"}
    for attempt in range(6):
        async with session.post(url, json={"user_id": user_id}, headers=headers) as resp:
            body = await resp.json()
            if resp.status == 200:
                return
            if body.get("errcode") in ("M_FORBIDDEN", "M_ALREADY_IN_ROOM"):
                return
            if body.get("errcode") == "M_LIMIT_EXCEEDED":
                wait = (body.get("retry_after_ms", 2000) / 1000) + 0.5
                await asyncio.sleep(wait)
                continue
            logger.warning("  Invite %s to %s: %s", user_id, room_id, body)
            return


async def send_welcome(session: aiohttp.ClientSession, token: str, room_id: str, msg: str):
    url = f"{MATRIX_HOMESERVER}/_matrix/client/v3/rooms/{room_id}/send/m.room.message/1"
    headers = {"Authorization": f"Bearer {token}"}
    async with session.put(url, json={"msgtype": "m.text", "body": msg}, headers=headers) as resp:
        await resp.json()


async def main():
    logger.info("=== mzgb Agent Bootstrap ===")
    logger.info("Homeserver: %s", MATRIX_HOMESERVER)

    async with aiohttp.ClientSession() as session:
        # 1. Register all agents
        logger.info("\n[1/4] Registering agent accounts...")
        for name, cfg in AGENTS.items():
            await register_agent(session, cfg["username"], cfg["password"])
            await asyncio.sleep(1.5)

        # 2. Login as first agent (Natnael — infra) to create rooms
        logger.info("\n[2/4] Logging in as Natnael to create rooms...")
        token = await login_agent(session, "natnael", AGENTS["natnael"]["password"])

        # 3. Create all rooms and ensure they are public
        logger.info("\n[3/4] Creating Matrix rooms...")
        room_ids = {}
        for key, alias in ROOMS.items():
            room_ids[key] = await create_room(session, token, alias)
            if room_ids[key]:
                await set_room_public(session, token, room_ids[key])
                await asyncio.sleep(0.5)

        # 4. Invite all agents to all rooms
        logger.info("\n[4/4] Inviting all agents to all rooms...")
        for name, cfg in AGENTS.items():
            user_id = f"@{cfg['username']}:localhost"
            for key, room_id in room_ids.items():
                if room_id:
                    await invite_to_room(session, token, room_id, user_id)
            logger.info("  %s invited to all rooms ✓", name)

        # Welcome message
        general_id = room_ids.get("general", "")
        if general_id:
            await send_welcome(session, token, general_id,
                "🎉 mzgb agent environment is ready!\n\n"
                "Agents:\n"
                "  • Biruk  (Backend)   — parser, filters, streaming\n"
                "  • Liya   (CLI)       — Click wiring, renderer\n"
                "  • Tigist (Features)  — buffer, follow, summary\n"
                "  • Natnael (Infra)    — scaffold, tests, README\n\n"
                "Rooms:\n"
                + "\n".join(f"  • {k}: {v}" for k, v in ROOMS.items()) +
                "\n\nStart agents: python3 agents/<name>.py"
            )

    logger.info("\n✅ Bootstrap complete. Start agents with: python3 agents/biruk.py (etc.)")


if __name__ == "__main__":
    asyncio.run(main())
