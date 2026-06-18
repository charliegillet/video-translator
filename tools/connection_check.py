#!/usr/bin/env python3
"""Connection check against a RocketRide engine (local-first).

Target resolution order:
  1. --uri <uri> argument, else
  2. auto-discover the IDE's LOCAL engine: find the `engine ... eaas.py` process
     and its LISTEN port via lsof -> http://localhost:<port>. Local engines run
     on an ephemeral port (--port=0) that changes per restart, so we discover it
     live each run, else
  3. ROCKETRIDE_URI from the environment / .env.

Local engines accept the SDK connection without a cloud token (no ROCKETRIDE_APIKEY
needed). Reports connected/authenticated and the node-catalog size.

    .venv/bin/python tools/connection_check.py [--uri URL]
"""
import asyncio
import os
import re
import subprocess
import sys


def discover_local_uri():
    try:
        pids = subprocess.check_output(
            ["pgrep", "-f", "engine .*eaas.py"], text=True, stderr=subprocess.DEVNULL
        ).split()
        if not pids:
            return None
        out = subprocess.check_output(
            ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN", "-a", "-p", pids[0]], text=True
        )
        m = re.search(r"127\.0\.0\.1:(\d+)", out)
        return f"http://localhost:{m.group(1)}" if m else None
    except Exception:
        return None


def count_services(svcs):
    if isinstance(svcs, list):
        return f"{len(svcs)} nodes"
    if isinstance(svcs, dict):
        for k in ("services", "data", "result", "nodes"):
            v = svcs.get(k)
            if isinstance(v, list):
                return f"{len(v)} nodes"
        return f"dict keys={list(svcs.keys())}"
    return f"type={type(svcs).__name__}"


async def main():
    from rocketride import RocketRideClient

    argv = sys.argv[1:]
    uri = argv[argv.index("--uri") + 1] if "--uri" in argv else None
    source = "argument"
    if not uri:
        uri = discover_local_uri()
        source = "auto-discovered local engine"
    if not uri:
        uri = os.environ.get("ROCKETRIDE_URI")
        source = "ROCKETRIDE_URI env/.env"
    if not uri:
        print("No engine target: no local eaas engine found, no --uri, no ROCKETRIDE_URI.")
        print("Start the RocketRide IDE in local mode, or pass --uri.")
        return 1

    print(f"target: {uri}  ({source})")
    client = RocketRideClient(uri=uri)
    try:
        await asyncio.wait_for(client.connect(), timeout=20)
    except Exception as e:
        print(f"RESULT: CONNECT FAILED -> {type(e).__name__}: {e}")
        return 1
    try:
        print(f"connected={client.is_connected()}  authenticated={client.is_authenticated()}")
        try:
            svcs = await asyncio.wait_for(client.get_services(), timeout=15)
            print(f"node catalog: {count_services(svcs)}")
        except Exception as e:
            print(f"get_services note: {type(e).__name__}: {e}")
        print("RESULT: OK - engine reachable")
        return 0
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
