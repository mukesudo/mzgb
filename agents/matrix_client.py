"""
Base Matrix client for LogSnap agents.
Uses matrix-nio (async Python Matrix client library).
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

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

    async def connect(self) -> None:
        """Login to the homeserver and set display name."""
        self.client = nio.AsyncClient(self.homeserver, f"@{self.username}:localhost")
        resp = await self.client.login(self.password)
        if isinstance(resp, nio.LoginError):
            raise RuntimeError(f"[{self.username}] Login failed: {resp.message}")
        await self.client.set_displayname(self.display_name)
        logger.info("[%s] Connected to %s", self.username, self.homeserver)

    async def join_room(self, room_alias: str) -> str:
        """Join a room by alias and cache its room_id. Returns room_id."""
        resp = await self.client.join(room_alias)
        if isinstance(resp, nio.JoinError):
            raise RuntimeError(f"[{self.username}] Could not join {room_alias}: {resp.message}")
        room_id = resp.room_id
        self._room_ids[room_alias] = room_id
        logger.info("[%s] Joined %s (%s)", self.username, room_alias, room_id)
        return room_id

    async def send(self, room_alias: str, message: str) -> None:
        """Send a plain-text message to a room."""
        room_id = self._room_ids.get(room_alias)
        if not room_id:
            room_id = await self.join_room(room_alias)
        resp = await self.client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message},
        )
        if isinstance(resp, nio.RoomSendError):
            logger.error("[%s] Send failed in %s: %s", self.username, room_alias, resp.message)

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
