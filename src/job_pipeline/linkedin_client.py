"""Fetch full LinkedIn job postings through the LinkedIn MCP server.

Uses mcp-server-linkedin by Daniel Sticker
(https://github.com/stickerdaniel/linkedin-mcp-server),
Copyright 2025-2026 Daniel Sticker, licensed under the Apache License 2.0.
Pinned to v4.26.2; the server runs as a separate process over stdio and is
not bundled or modified here.

Note: the server drives a logged-in browser session. LinkedIn's User Agreement
prohibits automated access, so keep runs small and human-paced
(see max_per_run and delay_seconds in config/settings.yaml).
"""

import asyncio
import json
import logging
import random
import shutil
import subprocess

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from job_pipeline import store

log = logging.getLogger(__name__)


def fetch_postings(conn, cfg: dict, interactive: bool = False) -> int:
    """Fetch full postings for pending jobs. Returns how many were saved."""
    job_ids = store.pending_ids(conn, cfg["max_per_run"])
    if not job_ids:
        return 0
    print(f"Fetching {len(job_ids)} postings from LinkedIn...")
    done, needs_login = asyncio.run(_fetch_all(conn, job_ids, cfg))

    if needs_login:
        if not interactive:
            print("LinkedIn session expired. Run `uv run jobs login`, then `uv run jobs run`.")
            return done
        login(cfg)
        remaining = store.pending_ids(conn, cfg["max_per_run"] - done)
        more, _ = asyncio.run(_fetch_all(conn, remaining, cfg))
        done += more
    return done

def login(cfg: dict) -> None:
    """Open the LinkedIn login window and block until it's done."""
    print("Opening LinkedIn login window. Sign in, then close it...")
    subprocess.run(
        [_resolve_user(cfg["command"]), *cfg["args"], "--login"], check=True
    )
    print("LinkedIn session saved.")

def _resolve_user(name: str) -> str:
    """Find the executable on PATH, e.g. 'uvx' -> 'C:\\Users\\...\\uvx.exe'."""
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(
            f"'{name}' not found on PATH. Install uv or put the full path "
            f"in config/settings.yaml under linkedin.command."
        )
    return path

def _unpack(result) -> dict:
    """Get the tool's dict back, whichever way the server sent it."""
    data = _field(result, "structured_content", "structuredContent")
    if not data:
        data = json.loads(result.content[0].text)
    if not isinstance(data, dict):
        raise TypeError(f"Unexpected result shape: {str(data)[:300]}")
    return data


def _field(result, *names):
    for name in names:
        if hasattr(result, name):
            return getattr(result, name)
        
    return None
        

async def _fetch_all(conn, job_ids: list[str], cfg: dict) -> int:

    server = StdioServerParameters(
        command=_resolve_user(cfg["command"]), args=cfg["args"]
    )

    done = 0

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()

            for n, job_id in enumerate(job_ids, 1):
                try:

                    result = await session.call_tool(
                        "get_job_details", {"job_id": job_id}
                    )

                    if _field(result, "is_error", "isError"):
                        raise RuntimeError(result.content[0].text)
                    
                    data = _unpack(result)
                    text = data.get("sections", {}).get("job_posting", "")
                    apply_state = (data.get("apply") or {}).get("type")

                    store.save_posting(conn, job_id, text, apply_state)

                    done += 1

                    print(f"  [{n}/{len(job_ids)}] {job_id} ok"
                          + (f" ({apply_state})" if apply_state else ""))
                    
                except Exception as e:
                    msg = str(e)
                    if "session expired" in msg.lower() or "login window" in msg.lower():
                        return done, True
                    log.warning("Failed %s: %s", job_id, msg)
                    print(f"  [{n}/{len(job_ids)}] {job_id} FAILED")

                if n < len(job_ids):
                    await asyncio.sleep(random.uniform(*cfg["delay_seconds"]))

    return done, False

