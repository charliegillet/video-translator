# Polyglot Cup — project state / handoff

**Last updated:** 2026-06-18 (launch day). **Owner:** Charlie Gillet.
**Read this first if you are a fresh Claude session opened in this folder.** It is self-contained: everything you need to continue is here or linked below.

---

## What this is
A **1-minute live booth demo** for **RocketRide Launch Night** (Shack15, SF, evening of June 18 2026).

**Concept ("Polyglot Cup"):** ONE RocketRide **cloud** pipeline parallel-transcribes ~30 short (<1 min) World Cup **fan** clips in their native languages, then an LLM **translates each to English and tags the funniest / most-exciting moment**. It shows multimodal + multilingual + "any model, no lock-in" in one run. **Closer:** swap `llm_anthropic` → `llm_openai` in one line, live, while the same Whisper model server keeps running underneath.

**Decisions made:**
- Going with **Polyglot Cup** (it was the operator's featured pick; the debate's judge ranked it joint-last on feasibility, see the debate log for the honest critique, but Charlie chose it).
- **Build the dropper variant FIRST** (zero client code, most reliable). Add the fancier custom SSE grid later only if there's time.
- **Connection mode: LOCAL** (switched 2026-06-18). Now runs against the IDE-managed local engine, not cloud. See "Connection mode: LOCAL" under Status. The same `.pipe` runs on either; only the endpoint differs.

---

## Status

### Done
- Folder scaffolded and **self-contained** (catalog, schema, validator, `.env`, per-language `clips/` dirs).
- `pipelines/polyglot.pipe` **authored and VALIDATED 1/1** against the live `services-catalog.json`.
- Chain: `dropper → parse → audio_transcribe → question → prompt → llm_anthropic → response_answers`.

### Two corrections already baked into the pipe (the PLAN's skeleton was wrong on both)
1. `audio_transcribe` profile key is **`model`** (e.g. `"model": "base"`), NOT `mode`. Verified against every working pipe in the testing ground.
2. `prompt`'s `text` input produces nothing (catalog lane `text: []`); it only emits `questions` from a `questions` input. So the transcript (`text`) goes through a **`question` node** (`text → questions`) first, then `prompt` injects the translate-and-tag instruction. (The PLAN doc still shows the old, wrong skeleton; patching it is an open TODO.)

### Connection mode: LOCAL (switched 2026-06-18) — CURRENT
Now targeting the **IDE-managed local engine**, not cloud.
- The RocketRide IDE (local mode) runs the engine at `~/Library/Application Support/RocketRide/engine` (server-v3.2.2). It binds an **ephemeral port** (`--port=0`, was 58202) that changes per restart, so discover it live.
- **Python SDK works locally:** `rocketride 1.2.0` installed in `.venv/`. `tools/connection_check.py` auto-discovers the engine port and connects with NO cloud token. Verified: `connected=True authenticated=True → RESULT: OK`.
- **Local catalog:** `.rocketride/services-catalog.json` refreshed to the local engine (102 nodes); all 7 pipe nodes present; both pipes validate 2/2 (static).
- **Booth path (recommended): run the pipe in the RocketRide IDE** (dropper opens in the browser). The IDE manages the ephemeral-port engine; this is the zero-client-code variant and already runs locally.
- **OpenAI key:** `llm_openai` uses `${ROCKETRIDE_OPENAI_KEY}` (set in gitignored `.env`). In IDE/local mode, make sure the engine actually receives it (extension env sync / project `.env`). NEVER paste the literal key into the canvas: it gets written into the `.pipe` and committed (happened once, see git `5b8c1fc`; reverted in `1efb7b5`).
- **Known SDK skew:** SDK 1.2.0 vs engine 3.2.2 — the SDK's `validate()` / `get_services()` response shapes don't fully line up (engine `validate()` returns a spurious `ccode 40`). Treat the static validators (`tools/validate_pipes.py`, skill `--static`) plus the live IDE run as authoritative; pin the SDK to the engine version if you need SDK `validate()` or scripted `send_files()` runs.

### Clips: DONE (2026-06-18) — CURRENT
All booth clips are downloaded, curated (every clip human listen-checked), and grouped by spoken language in `clips/<lang>/` (gitignored, not in the repo). **37 clips across 8 languages:**

| lang | clips |
|---|---|
| en | 9 |
| es | 8 |
| pt | 6 |
| de | 4 |
| ar | 3 |
| fr | 3 |
| ko | 3 |
| ja | 1 |

- Every clip is ≤60s with verified audio (no silent clips); grouped by language so Whisper `language` is set per folder.
- Changes from the original 6-language plan: **Norwegian (`no`) dropped** — no clean Norwegian-speech UGC exists in-window (the viral escalator clip is English news coverage). **English (`en`), Arabic (`ar`), Korean (`ko`) added** as bonuses. **Japanese (`ja`) is thin at 1** — on-site JP content is overwhelmingly stadium roar, not single-speaker speech.
- **English clips are NOT translated** (English in → English out); they round out the grid. 4 of the 9 are short FIFA goal Shorts (little speech, FIFA Content-ID); 5 are English-creator commentary with real talking.
- Sourcing method: per-language agent passes with YouTube auto-caption + volume verification, then human ear-check. **Sourcing is COMPLETE.**
- Possible follow-up: some clips are exactly 60s; may shorten to strictly `<1 min` if needed.

### Pending to go LIVE — CLOUD path (SUPERSEDED by LOCAL mode above; kept for reference)
1. Generate a cloud API key: cloud.rocketride.ai → API Keys → Create.
2. Fill `.env` (already exists, copied from `.env.example`):
   - `ROCKETRIDE_APIKEY=<cloud key>`
   - `ROCKETRIDE_ANTHROPIC_KEY=<anthropic key>`
   - `ROCKETRIDE_OPENAI_KEY=<openai key>`  ← for the live model-swap closer
   - `ROCKETRIDE_URI=https://api.rocketride.ai` is already set.
3. `pip3 install rocketride` (the Python client; not yet installed).
4. Then: live connection check + push ONE test clip end-to-end to confirm transcription + translation behave before committing to all 30.

### Build steps not yet done (no creds needed for most)
- ~~Download ~30 fan clips via `yt-dlp` into `clips/<lang>/`.~~ **DONE** — 37 clips / 8 languages; see "Clips: DONE" above.
- `driver.py`: `client.use(..., ttl=0, use_existing=True)` once + the dropper flow (or `send_files` for the scripted/grid variant).
- Patch the stale `.pipe` skeleton in `PLAN-polyglot-cup.md`.
- (Optional, later) custom SSE grid UI for the cascade visual (variant B).

---

## How to validate the pipe offline (no creds needed)
```bash
python3 /Users/charlie/rocketride/polyglot-cup/tools/validate_pipes.py /Users/charlie/rocketride/polyglot-cup
```
Expect `=== VALID: 1/1 positive pipes ===`. The validator checks every `pipelines/**/*.pipe` against `.rocketride/services-catalog.json` (a snapshot of the connected cloud server; refreshes when the IDE connects).

---

## Key gotchas (do not relearn these the hard way)
- **No YouTube/URL/web ingest node exists.** Clips MUST be pre-downloaded to local files. `dropper` (drag-drop, booth) or `webhook` + `client.send_files()` (scripted). `filesys://` does NOT run on cloud.
- **"Parallel" = orchestration fan-out through ONE shared, warm Whisper model behind a global lock, NOT 30 GPUs.** Say it that way on stage; the technical crowd will catch a 30x claim.
- **Idle death:** cloud pipelines die after ~15 min idle. Set `ttl=0` in `.use()`. Start ONCE with `use_existing=True`; never use/terminate per attendee.
- **Cold start:** warm the pipeline with 1-2 throwaway clips before doors (Whisper loads on first use).
- **Never block the async loop** (no `input()`, `time.sleep`, sync `requests`): freezes the websocket, connection drops ~60s. Use `asyncio.sleep` / `run_in_executor`.
- **Accuracy = the governance pitch:** instruct the LLM to abstain (language `unclear`, empty moment) rather than guess. Cross-lingual accuracy is THE risk of this concept (why the judge ranked it last); de-risk by curating clean-audio clips and grouping by language.
- **Rights:** fan/creator UGC only, NOT FIFA/FOX/Telemundo broadcast (Content-ID). Treat as transient internal demo footage.
- **Honest framing on stage:** never "paste a YouTube link / happening right now" (clips are pre-staged); "the model swap is what's live."

---

## YouTube search queries for clips (search Shorts, filter This week + Under 4 min, grab single-speaker fan UGC, ~5-6 clips per language)

| Lang | Native query (best for native audio) | English fallback |
|---|---|---|
| es | `Merlin pato México Mundial 2026 reacción` · `afición mexicana Mundial 2026` | `Merlin the duck Mexico jersey World Cup` |
| de | `deutsche Fans WM 2026 USA Reaktion` · `Fiago Freddy Buffalo Wild Wings` | `German fans Buffalo Wild Wings World Cup 2026` |
| no | `Norge fans rulletrapp robåt VM 2026` | `Norway fans rowing escalator World Cup Boston` |
| pt | `torcida Brasil Copa do Mundo 2026 reação` | `Brazil fans reaction World Cup 2026` |
| ja | `日本 サポーター ワールドカップ2026 反応` | `Japan fans World Cup 2026 reaction` |
| fr | `supporters Coupe du Monde 2026 réaction` | `France/Canada fans World Cup 2026 reaction` |
| pad | `World Cup 2026 fans first American food reaction` | `World Cup 2026 fan reactions compilation shorts` |

Prioritize **one clear speaker** over stadium roar (crowd noise transcribes to garbage). After download: trim to <60s, sort into `clips/<lang>/`, listen-check, drop garbled ones.

---

## Files in this folder
- `PLAN-polyglot-cup.md` — the full build-ready plan (note: its `.pipe` skeleton is the OLD/wrong one; the validated truth is `pipelines/polyglot.pipe`).
- `rocketride-launch-demo-debate-log.md` — the 6-agent debate (5 pitches + devil's advocate + verdict) that produced this concept. Read the verdict + DA thesis for the honest case for/against.
- `pipelines/polyglot.pipe` — the validated dropper pipeline (source of truth).
- `tools/validate_pipes.py` — offline structural validator.
- `.rocketride/` — services-catalog.json + schema (the live cloud node catalog).
- `clips/{en,es,pt,de,ar,fr,ko,ja}/` — the 37 downloaded booth clips (gitignored), grouped by spoken language. See "Clips: DONE".
- `.env` / `.env.example` — credentials (`.env` is gitignored).

---

## Suggested next action for a fresh session
1. Confirm the pipe still validates (command above).
2. Clips are DONE (see "Clips: DONE") — run the pipe in the RocketRide IDE (local engine) on the `clips/<lang>/` folders, or use `tools/connection_check.py` to verify the local engine, then push a test clip.
3. Remaining open items: patch the stale `.pipe` skeleton in `PLAN-polyglot-cup.md`; optionally shorten clips to strictly `<1 min`; optional Japanese depth (ja=1).

> Note on resuming: this folder is its OWN Claude Code project. The original brainstorm session lives under the `rocketride-server` project and will NOT appear in `/resume` here. That's expected; this STATE.md + the two docs above carry the full context.
