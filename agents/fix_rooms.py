"""
fix_rooms.py — One-shot script to make all LogSnap rooms public
and invite your personal account so you can join from Element.

Usage:
    python3 agents/fix_rooms.py --your-username YOUR_MATRIX_USERNAME
"""

import asyncio
import sys
import argparse
import logging
from pathlib import Path

import aiohttp

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.config import AGENTS, MATRIX_HOMESERVER, ROOMS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("fix_rooms")


async def login(session, username, password):
    url = f"{MATRIX_HOMESERVER}/_matrix/client/v3/login"
    async with session.post(url, json={
        "type": "m.login.password",
        "identifier": {"type": "m.id.user", "user": username},
        "password": password,
    }) as resp:
        body = await resp.json()
        token = body.get("access_token")
        if not token:
            raise RuntimeError(f"Login failed: {body}")
        logger.info("  Logged in as %s ✓", username)
        return token


async def resolve_alias(session, token, alias):
    encoded = alias.replace("#", "%23")
    url = f"{MATRIX_HOMESERVER}/_matrix/client/v3/directory/room/{encoded}"
    async with session.get(url, headers={"Authorization": f"Bearer {token}"}) as resp:
        body = await resp.json()
        return body.get("room_id")


async def set_public(session, token, room_id, alias):
    url = f"{MATRIX_HOMESERVER}/_matrix/client/v3/rooms/{room_id}/state/m.room.join_rules"
    async with session.put(url,
        json={"join_rule": "public"},
        headers={"Authorization": f"Bearer {token}"}
    ) as resp:
        if resp.status == 200:
            logger.info("  ✓ %s → public", alias)
        else:
            body = await resp.json()
            logger.warning("  ✗ %s: %s", alias, body)


async def invite_user(session, token, room_id, user_id):
    url = f"{MATRIX_HOMESERVER}/_matrix/client/v3/rooms/{room_id}/invite"
    async with session.post(url,
        json={"user_id": user_id},
        headers={"Authorization": f"Bearer {token}"}
    ) as resp:
        body = await resp.json()
        if resp.status == 200:
            logger.info("  ✓ Invited %s", user_id)
        elif body.get("errcode") in ("M_ALREADY_IN_ROOM", "M_FORBIDDEN"):
            logger.info("  ~ %s already in room or pending", user_id)
        else:
            logger.warning("  ✗ Could not invite %s: %s", user_id, body)


async def main(your_username: str):
    async with aiohttp.ClientSession() as session:
        token = await login(session, "natnael", AGENTS["natnael"]["password"])

        logger.info("\nSetting all rooms to public...")
        room_ids = {}
        for key, alias in ROOMS.items():
            room_id = await resolve_alias(session, token, alias)
            if room_id:
                room_ids[key] = room_id
                await set_public(session, token, room_id, alias)
            else:
                logger.warning("  Could not resolve %s", alias)

        if your_username:
            user_id = f"@{your_username}:localhost"
            logger.info("\nInviting %s to all rooms...", user_id)
            for key, room_id in room_ids.items():
                await invite_user(session, token, room_id, user_id)

    logger.info("\n✅ Done! All rooms are now public.")
    logger.info("In Element: click '+' → 'Join public room' → search 'logsnap'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--your-username", default="", help="Your Matrix username (without @:localhost)")
    args = parser.parse_args()
    asyncio.run(main(args.your_username))
