import asyncio
import os
from pathlib import Path

HEARTBEAT_FILE = Path(os.environ.get("BOT_HEARTBEAT_FILE", "/tmp/bot_heartbeat"))
HEARTBEAT_INTERVAL = int(os.environ.get("BOT_HEARTBEAT_INTERVAL", "30"))


async def heartbeat_loop() -> None:
    HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            HEARTBEAT_FILE.touch()
        except Exception:
            pass
        await asyncio.sleep(HEARTBEAT_INTERVAL)
