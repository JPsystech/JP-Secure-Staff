"""
Backend server startup script.

CRITICAL: On Windows, event loop policy must be set BEFORE uvicorn starts.
This ensures Playwright's async subprocess operations work correctly.
"""
import sys
import asyncio

# CRITICAL FIX for Windows: Set event loop policy BEFORE uvicorn creates event loop
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

