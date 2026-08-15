#!/usr/bin/env python3
"""Antigravity Figma Live Bridge Server.

Runs a local HTTP/WebSocket proxy on localhost:9099.
Allows Antigravity to send commands directly into the active Figma canvas via the
Figma Live Bridge Plugin.
"""

from __future__ import annotations

import asyncio
import json
import sys
from aiohttp import web

HOST = "localhost"
PORT = 9099

connected_sockets = set()


async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    connected_sockets.add(ws)
    print(f"[+] Figma Plugin connected! (Active connections: {len(connected_sockets)})")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                print(f"[Figma Plugin -> Host]: {msg.data}")
            elif msg.type == web.WSMsgType.ERROR:
                print(f"[-] WebSocket error: {ws.exception()}")
    finally:
        connected_sockets.remove(ws)
        print(f"[-] Figma Plugin disconnected. (Active connections: {len(connected_sockets)})")

    return ws


async def push_command_handler(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
        if not connected_sockets:
            return web.json_response(
                {"status": "error", "message": "No active Figma Plugin connected. Please run the plugin in Figma."},
                status=503
            )

        message_str = json.dumps(payload)
        for ws in list(connected_sockets):
            await ws.send_str(message_str)

        print(f"[+] Dispatched command to {len(connected_sockets)} Figma instance(s): {payload.get('action')}")
        return web.json_response({"status": "ok", "delivered_to": len(connected_sockets)})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", websocket_handler)
    app.router.add_post("/push", push_command_handler)
    return app


def main():
    print(f"[*] Starting Antigravity Figma Live Bridge on http://{HOST}:{PORT} ...")
    app = create_app()
    web.run_app(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
