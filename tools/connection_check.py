#!/usr/bin/env python3
"""Connection check against the RocketRide cloud engine.

Reads ROCKETRIDE_URI + ROCKETRIDE_APIKEY from .env in the current directory
(the Python SDK loads .env from cwd), connects, and reports auth + a couple of
lightweight authenticated calls. Prints no secrets.

Run from the project root with the venv python:
    .venv/bin/python tools/connection_check.py
"""
import asyncio
import os
import sys


def _mask(v):
    if not v:
        return "(unset)"
    return v[:10] + "..." if len(v) > 12 else v


async def main():
    try:
        from rocketride import RocketRideClient, AuthenticationException
    except Exception as e:
        print(f"SDK import failed: {e}")
        return 2

    print(f"ROCKETRIDE_URI    = {os.environ.get('ROCKETRIDE_URI', '(from .env)')}")
    apikey = os.environ.get("ROCKETRIDE_APIKEY")
    print(f"ROCKETRIDE_APIKEY = {_mask(apikey)} (env; client also reads .env)")
    if apikey in (None, "your-api-key-here", "your-api-key"):
        print("WARNING: ROCKETRIDE_APIKEY looks like the placeholder; auth will likely fail.")

    client = RocketRideClient()
    try:
        await asyncio.wait_for(client.connect(), timeout=30)
    except AuthenticationException as e:
        print(f"RESULT: AUTH FAILED -> {e}")
        return 1
    except asyncio.TimeoutError:
        print("RESULT: CONNECT TIMEOUT (30s) - endpoint unreachable / network blocked")
        return 1
    except Exception as e:
        print(f"RESULT: CONNECT ERROR -> {type(e).__name__}: {e}")
        return 1

    try:
        connected = client.is_connected()
        authed = client.is_authenticated()
        print(f"connected={connected}  authenticated={authed}")
        if not authed:
            print("RESULT: connected but NOT authenticated (check ROCKETRIDE_APIKEY).")
            return 1
        info = await asyncio.wait_for(client.get_server_info(), timeout=20)
        print(f"server_info: {info}")
        svcs = await asyncio.wait_for(client.get_services(), timeout=20)
        try:
            count = len(svcs)
        except Exception:
            count = "?"
        print(f"get_services: {count} nodes available")
        print("RESULT: OK - connected, authenticated, engine reachable")
        return 0
    except Exception as e:
        print(f"RESULT: POST-CONNECT CALL ERROR -> {type(e).__name__}: {e}")
        return 1
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
