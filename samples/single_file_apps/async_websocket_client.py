"""
WebSocket Chat Client - A QtPie async chat room demo.

Usage:
    1. Start the server:  uv run python samples/single_file_apps/async_websocket_server.py
    2. Run this client:   uv run python samples/single_file_apps/async_websocket_client.py
    3. Run MORE clients in separate terminals to see presence + chat!

This demonstrates why async is essential. WITHOUT proper handling:
    - @asyncSlot: Coroutines never await, buttons do nothing
    - @asyncClose: WebSocket leaks, server never sees disconnect
    - async receive loop: UI freezes waiting for messages

Try removing @asyncSlot from on_connect() and watch it silently fail!
"""

import asyncio
import json
import random

import websockets
from qasync import asyncClose, asyncSlot  # type: ignore[import-untyped]
from qtpy.QtCore import Signal
from qtpy.QtGui import QCloseEvent
from qtpy.QtWidgets import QLabel, QLineEdit, QListWidget, QPushButton, QTextEdit, QWidget
from websockets.asyncio.client import ClientConnection

from qtpie import entry_point, make, widget

RANDOM_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Hank"]


@widget
class UsersPanel(QWidget):
    """Left panel: online users list."""

    label: QLabel = make(QLabel, "Online Users")
    users_list: QListWidget = make(QListWidget)


@widget
class ChatPanel(QWidget):
    """Right panel: messages and input."""

    # Signals for parent to handle
    connect_requested = Signal()
    disconnect_requested = Signal()
    send_requested = Signal(str)

    status: QLabel = make(QLabel, "Disconnected")
    messages: QTextEdit = make(QTextEdit, readOnly=True)
    message_input: QLineEdit = make(QLineEdit, placeholderText="Type a message...", returnPressed="on_send")
    send_btn: QPushButton = make(QPushButton, "Send", clicked="on_send", enabled=False)
    connect_btn: QPushButton = make(QPushButton, "Connect", clicked="on_connect")
    disconnect_btn: QPushButton = make(QPushButton, "Disconnect", clicked="on_disconnect", enabled=False)

    def on_connect(self) -> None:
        self.connect_requested.emit()

    def on_disconnect(self) -> None:
        self.disconnect_requested.emit()

    def on_send(self) -> None:
        text = self.message_input.text().strip()
        if text:
            self.message_input.clear()
            self.send_requested.emit(text)


@entry_point
@widget(layout="horizontal")
class ChatClient(QWidget):
    """WebSocket chat client with presence awareness."""

    users_panel: UsersPanel = make(UsersPanel)
    chat_panel: ChatPanel = make(
        ChatPanel,
        connect_requested="on_connect",
        disconnect_requested="on_disconnect",
        send_requested="on_send",
    )

    _ws: ClientConnection | None = None
    _task: asyncio.Task[None] | None = None
    _username: str = ""

    def setup(self) -> None:
        self._username = random.choice(RANDOM_NAMES) + str(random.randint(1, 99))
        self.setWindowTitle(f"Chat - {self._username}")
        self.resize(600, 400)

    @asyncSlot()
    async def on_connect(self) -> None:
        if self._ws is not None:
            return

        self.chat_panel.connect_btn.setEnabled(False)
        self.chat_panel.status.setText("Connecting...")

        try:
            self._ws = await websockets.connect("ws://localhost:8765")
            self.chat_panel.status.setText(f"Connected as {self._username}")
            self.chat_panel.disconnect_btn.setEnabled(True)
            self.chat_panel.send_btn.setEnabled(True)
            self.chat_panel.message_input.setEnabled(True)

            await self._ws.send(json.dumps({"type": "join", "name": self._username}))
            self._task = asyncio.create_task(self._receive_loop())

        except Exception as e:
            self.chat_panel.status.setText(f"Error: {e}")
            self.chat_panel.connect_btn.setEnabled(True)

    @asyncSlot()
    async def on_disconnect(self) -> None:
        await self._cleanup()
        self.chat_panel.status.setText("Disconnected")
        self.chat_panel.connect_btn.setEnabled(True)
        self.chat_panel.disconnect_btn.setEnabled(False)
        self.chat_panel.send_btn.setEnabled(False)
        self.users_panel.users_list.clear()

    @asyncSlot(str)
    async def on_send(self, text: str) -> None:
        if self._ws is None:
            return
        await self._ws.send(json.dumps({"type": "message", "text": text}))

    async def _receive_loop(self) -> None:
        if self._ws is None:
            return

        try:
            async for raw in self._ws:
                msg = json.loads(raw)

                if msg["type"] == "join":
                    self.chat_panel.messages.append(f">>> {msg['user']} joined the chat")
                elif msg["type"] == "leave":
                    self.chat_panel.messages.append(f"<<< {msg['user']} left the chat")
                elif msg["type"] == "message":
                    self.chat_panel.messages.append(f"[{msg['user']}] {msg['text']}")
                elif msg["type"] == "users":
                    self.users_panel.users_list.clear()
                    for user in msg["users"]:
                        self.users_panel.users_list.addItem(user)

        except websockets.ConnectionClosed:
            self.chat_panel.status.setText("Connection lost")
            self.chat_panel.connect_btn.setEnabled(True)
            self.chat_panel.disconnect_btn.setEnabled(False)
            self.chat_panel.send_btn.setEnabled(False)
        except asyncio.CancelledError:
            pass

    async def _cleanup(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        if self._ws is not None:
            await self._ws.close()
            self._ws = None

    @asyncClose
    async def closeEvent(self, event: QCloseEvent) -> None:  # type: ignore[override]
        await self._cleanup()
