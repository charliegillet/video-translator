#!/usr/bin/env python3
"""Deterministic structural validator for every .pipe in the testing ground.

Validates each pipe against the connected server's services-catalog.json:
  - JSON validity + required top-level fields (components/project_id/version)
  - unique component ids; providers exist in the catalog
  - exactly one source component, with a correct source config shape
  - input.from references resolve; lane is produced by `from` AND accepted by target
  - control.from references resolve
  - invoke requirements satisfied (agent has its llm/memory; min/max respected)
  - project_id is a valid UUID, unique across the whole folder
  - no orphan components

Usage: python3 tools/validate_pipes.py [root_dir]
Exit 0 only when every pipe passes. Files under any _negative/ dir are checked
to be INTENTIONALLY invalid (they must FAIL) and reported separately.
"""
import json, os, sys, glob, re, uuid as uuidmod

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, ".rocketride", "services-catalog.json")

catalog = {e["name"]: e for e in json.load(open(CATALOG))}

def is_source(prov):
    return "source" in (catalog.get(prov, {}).get("classType") or [])

def input_lanes(prov):
    lanes = catalog.get(prov, {}).get("lanes", {}) or {}
    return set(k for k in lanes.keys() if k != "_source")

def output_lanes(prov):
    lanes = catalog.get(prov, {}).get("lanes", {}) or {}
    out = set()
    for k, v in lanes.items():
        out |= set(v or [])
    return out

def invoke_reqs(prov):
    return catalog.get(prov, {}).get("invoke", {}) or {}

def validate_pipe(path):
    errs, warns = [], []
    try:
        raw = open(path).read()
        d = json.loads(raw)
    except Exception as e:
        return [f"invalid JSON: {e}"], [], None

    comps = d.get("components")
    if not isinstance(comps, list) or not comps:
        errs.append("missing/empty 'components' array")
        return errs, warns, None
    if "project_id" not in d:
        errs.append("missing 'project_id'")
    pid = d.get("project_id")
    if pid is not None:
        try:
            uuidmod.UUID(str(pid))
        except Exception:
            errs.append(f"project_id is not a valid UUID: {pid!r}")
    if d.get("version") != 1:
        warns.append(f"version != 1 ({d.get('version')})")

    ids = [c.get("id") for c in comps]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        errs.append(f"duplicate component ids: {dupes}")
    idset = set(ids)

    # provider validity + source config shape
    sources = []
    for c in comps:
        prov = c.get("provider")
        cid = c.get("id")
        if prov not in catalog:
            errs.append(f"[{cid}] unknown provider '{prov}' (not in catalog)")
            continue
        if not isinstance(c.get("config"), dict):
            errs.append(f"[{cid}] config must be an object")
        if is_source(prov):
            sources.append(cid)
            cfg = c.get("config", {})
            for k in ("mode", "type"):
                if k not in cfg:
                    warns.append(f"[{cid}] source config missing '{k}'")
            if cfg.get("type") != prov:
                warns.append(f"[{cid}] source config.type '{cfg.get('type')}' != provider '{prov}'")
    if len(sources) == 0:
        errs.append("no source component (need exactly one)")
    elif len(sources) > 1:
        warns.append(f"multiple source components: {sources}")
    if d.get("source") and d["source"] not in idset:
        errs.append(f"top-level 'source' '{d['source']}' is not a component id")

    # lane + control wiring
    referenced = set()
    invoke_edges = {}  # target_id -> {classType: [invoker_ids]}
    for c in comps:
        prov = c.get("provider"); cid = c.get("id")
        for inp in c.get("input", []) or []:
            frm = inp.get("from"); lane = inp.get("lane")
            referenced.add(frm)
            if frm not in idset:
                errs.append(f"[{cid}] input.from '{frm}' is not a component id")
                continue
            src_prov = next((x.get("provider") for x in comps if x.get("id") == frm), None)
            if src_prov in catalog and lane not in output_lanes(src_prov) and not is_source(src_prov):
                errs.append(f"[{cid}] input lane '{lane}' not produced by '{frm}' ({src_prov})")
            if src_prov in catalog and is_source(src_prov):
                src_out = set((catalog[src_prov]["lanes"].get("_source")) or [])
                if lane not in src_out:
                    errs.append(f"[{cid}] input lane '{lane}' not produced by source '{frm}' ({src_prov}); produces {sorted(src_out)}")
            if prov in catalog and not is_source(prov) and lane not in input_lanes(prov) and input_lanes(prov):
                errs.append(f"[{cid}] provider '{prov}' does not accept input lane '{lane}'; accepts {sorted(input_lanes(prov))}")
        for ctl in c.get("control", []) or []:
            frm = ctl.get("from"); ct = ctl.get("classType")
            referenced.add(frm)
            if frm not in idset:
                errs.append(f"[{cid}] control.from '{frm}' is not a component id")
                continue
            invoke_edges.setdefault(frm, {}).setdefault(ct, []).append(cid)

    # invoke satisfaction (agent needs its llm/memory, etc.)
    for c in comps:
        prov = c.get("provider"); cid = c.get("id")
        reqs = invoke_reqs(prov)
        if not reqs:
            continue
        got = invoke_edges.get(cid, {})
        for ct, spec in reqs.items():
            n = len(got.get(ct, []))
            mn = spec.get("min", 0); mx = spec.get("max")
            if n < mn:
                errs.append(f"[{cid}] '{prov}' needs >= {mn} '{ct}' control connection(s), has {n}")
            if mx is not None and n > mx:
                errs.append(f"[{cid}] '{prov}' allows <= {mx} '{ct}' control connection(s), has {n}")

    # orphan check: every non-source comp must connect in or be referenced out
    for c in comps:
        cid = c.get("id"); prov = c.get("provider")
        if cid in sources:
            continue
        has_in = bool(c.get("input")) or bool(c.get("control"))
        if not has_in and cid not in referenced:
            errs.append(f"[{cid}] orphan component (no input, no control, not referenced)")

    return errs, warns, pid

def main():
    pipes = sorted(glob.glob(os.path.join(ROOT, "pipelines", "**", "*.pipe"), recursive=True))
    pos = [p for p in pipes if os.sep + "_negative" + os.sep not in p]
    neg = [p for p in pipes if os.sep + "_negative" + os.sep in p]

    seen_pid = {}
    n_ok = 0; failures = []
    for p in pos:
        errs, warns, pid = validate_pipe(p)
        if pid:
            if pid in seen_pid:
                errs = (errs or []) + [f"duplicate project_id (also in {os.path.basename(seen_pid[pid])})"]
            else:
                seen_pid[pid] = p
        rel = os.path.relpath(p, ROOT)
        if errs:
            failures.append((rel, errs))
        else:
            n_ok += 1
            if warns:
                print(f"WARN {rel}: {warns}")

    print(f"\n=== VALID: {n_ok}/{len(pos)} positive pipes ===")
    for rel, errs in failures:
        print(f"\nFAIL {rel}")
        for e in errs:
            print(f"   - {e}")

    # negative pipes must fail
    if neg:
        print(f"\n=== NEGATIVE (must be invalid): {len(neg)} ===")
        for p in neg:
            errs, _, _ = validate_pipe(p)
            rel = os.path.relpath(p, ROOT)
            tag = "ok-invalid" if errs else "UNEXPECTED-VALID"
            print(f"   [{tag}] {rel}: {errs[0] if errs else 'no error found!'}")

    print(f"\nTOTAL pipes: {len(pipes)} ({len(pos)} positive + {len(neg)} negative)")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
