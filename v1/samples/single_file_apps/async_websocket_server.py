"""
WebSocket Chat Server - Run this first, then launch multiple clients.

Usage:
    uv run python samples/single_file_apps/async_websocket_server.py

This is a plain asyncio server (no Qt needed). It handles:
- User presence (join/leave notifications)
- Message broadcasting to all connected clients
- Online users list
"""

import asyncio
import json
from dataclasses import dataclass

import websockets
from websockets.asyncio.server import ServerConnection


@dataclass
class User:
    name: str
    ws: ServerConnection


# Connected users
users: dict[ServerConnection, User] = {}


async def broadcast(message: dict[str, str | list[str]]) -> None:
    """Send a message to all connected clients."""
    if not users:
        return
    payload = json.dumps(message)
    await asyncio.gather(*(user.ws.send(payload) for user in users.values()))


async def send_user_list() -> None:
    """Broadcast the current user list to all clients."""
    await broadcast(
        {
            "type": "users",
            "users": [user.name for user in users.values()],
        }
    )


async def handle_client(ws: ServerConnection) -> None:
    """Handle a single client connection."""
    user: User | None = None

    try:
        async for raw in ws:
            msg = json.loads(raw)

            if msg["type"] == "join":
                name = msg["name"]
                user = User(name=name, ws=ws)
                users[ws] = user
                print(f"[+] {name} joined ({len(users)} online)")

                # Notify everyone
                await broadcast({"type": "join", "user": name})
                await send_user_list()

            elif msg["type"] == "message" and user:
                print(f"[{user.name}] {msg['text']}")
                await broadcast(
                    {
                        "type": "message",
                        "user": user.name,
                        "text": msg["text"],
                    }
                )

    except websockets.ConnectionClosed:
        pass
    finally:
        if user and ws in users:
            del users[ws]
            print(f"[-] {user.name} left ({len(users)} online)")
            await broadcast({"type": "leave", "user": user.name})
            await send_user_list()


async def main() -> None:
    print("Chat server starting on ws://localhost:8765")
    print("Press Ctrl+C to stop\n")

    async with websockets.serve(handle_client, "localhost", 8765):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
