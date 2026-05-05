"""
Base Matrix client for mzgb agents.
Uses matrix-nio (async Python Matrix client library).
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional

import aiohttp
import nio

logger = logging.getLogger(__name__)


class AgentMatrixClient:
    """Wraps matrix-nio for agent use: login, join rooms, send/receive messages."""

    def __init__(self, homeserver: str, username: str, password: str, display_name: str):
        self.homeserver = homeserver
        self.username = username
        self.password = password
        self.display_name = display_name
        self.client: Optional[nio.AsyncClient] = None
        self._room_ids: dict[str, str] = {}
        self._access_token: str = ""

    async def connect(self) -> None:
        """Login to the homeserver and set display name."""
        self.client = nio.AsyncClient(self.homeserver, f"@{self.username}:localhost")
        resp = await self.client.login(self.password)
        if isinstance(resp, nio.LoginError):
            raise RuntimeError(f"[{self.username}] Login failed: {resp.message}")
        self._access_token = self.client.access_token
        # Initial sync so the client knows its room memberships
        await self.client.sync(timeout=5000)
        await self.client.set_displayname(self.display_name)
        logger.info("[%s] Connected to %s", self.username, self.homeserver)

    async def join_room(self, room_alias: str) -> str:
        """Join a room by alias and cache its room_id. Returns room_id."""
        for attempt in range(6):
            resp = await self.client.join(room_alias)
            if not isinstance(resp, nio.JoinError):
                room_id = resp.room_id
                self._room_ids[room_alias] = room_id
                logger.info("[%s] Joined %s (%s)", self.username, room_alias, room_id)
                return room_id
            # Rate limited — back off and retry
            if "limit" in resp.message.lower() or "too many" in resp.message.lower():
                wait = 5 * (attempt + 1)
                logger.warning("[%s] Rate limited joining %s, retrying in %ds...", self.username, room_alias, wait)
                await asyncio.sleep(wait)
                continue
            raise RuntimeError(f"[{self.username}] Could not join {room_alias}: {resp.message}")
        raise RuntimeError(f"[{self.username}] Failed to join {room_alias} after retries")

    async def send(self, room_alias: str, message: str) -> None:
        """Send a plain-text message to a room via direct HTTP (no sync state needed)."""
        room_id = self._room_ids.get(room_alias)
        if not room_id:
            room_id = await self.join_room(room_alias)
        txn_id = f"mzgb_{int(time.time() * 1000)}"
        url = f"{self.homeserver}/_matrix/client/v3/rooms/{room_id}/send/m.room.message/{txn_id}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        payload = {"msgtype": "m.text", "body": message}
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    body = await resp.json()
                    logger.error("[%s] Send failed in %s: %s", self.username, room_alias, body)

    async def send_status(self, room_alias: str, status: str, detail: str = "") -> None:
        """Send a structured status update."""
        ts = datetime.utcnow().strftime("%H:%M:%S UTC")
        msg = f"[{ts}] {self.display_name} | {status}"
        if detail:
            msg += f"\n  → {detail}"
        await self.send(room_alias, msg)

    async def listen(self, room_alias: str, callback) -> None:
        """
        Listen for new messages in a room and invoke callback(sender, body).
        Runs until cancelled.
        """
        room_id = self._room_ids.get(room_alias)
        if not room_id:
            room_id = await self.join_room(room_alias)

        async def on_message(room: nio.MatrixRoom, event: nio.RoomMessageText):
            if event.sender != f"@{self.username}:localhost":
                await callback(event.sender, event.body)

        self.client.add_event_callback(on_message, nio.RoomMessageText)
        logger.info("[%s] Listening in %s...", self.username, room_alias)
        await self.client.sync_forever(timeout=30000, full_state=True)

    async def disconnect(self) -> None:
        if self.client:
            await self.client.close()
            logger.info("[%s] Disconnected", self.username)
