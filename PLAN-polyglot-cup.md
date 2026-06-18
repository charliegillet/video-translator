# Polyglot Cup: one moment, every nation's voice, one English insight in 60 seconds (build-ready plan)

# Polyglot Cup — build-ready plan

**Demo:** ~30 short World Cup fan/creator clips in 5+ languages fan out into ONE RocketRide Cloud pipeline. Whisper transcribes each in its native language in parallel, an LLM translates every transcript to English and tags language + the one funniest/most-exciting moment, and the booth screen fills a grid: one global tournament, every nation's voice, rendered into one English insight feed. Closer: swap `llm_anthropic` to `llm_openai` in one line, live, while the same Whisper model server keeps running underneath.

**Status of this plan (CORRECTED 2026-06-18):** the source of truth is `pipelines/polyglot.pipe` (validated 1/1). This plan's original skeleton was wrong on two points and has been patched to match the validated pipe:
1. **The audio_transcribe config key is `model`, NOT `mode`.** The live driver reads it at `audio_transcribe/IGlobal.py:105` (`config.get('model', 'base')`). The node's internal `preconfig.profiles` block uses `mode` (which is what misled the original plan), but the driver never reads that key, and the generated schema (`transcribe.model`) plus every working pipe use `model`. Setting `mode` in a pipe is silently ignored.
2. **`prompt` cannot be fed from a `text` lane** (catalog lane `text: []` emits nothing). The transcript goes through a `question` node (`text -> questions`) first, then `prompt` injects the translate-and-tag instruction. See the corrected shape below.

Verify the rest against the LIVE cloud engine via `validate()` before the event (see Build Checklist).

---

## 1. Concept + why it wins this audience

The World Cup is live tonight (June 11 - July 19, hosted USA/Canada/Mexico). At an SF launch night, a duck in a Mexico jersey is the single most universally legible thing you can put on a screen. That earns the first 5 seconds from everyone walking past, jaded or not.

But this audience yawns at transcription, and they're right to: STT is a ~$4.4B commodity at 95%+ accuracy. So transcription is invisible plumbing here, not the pitch. The pitch is the thing on top that the commodity-STT players cannot do in one pipeline run:

**Multimodal AND multilingual in a single shot.** Whisper transcribes each clip in its source language, an LLM unifies all of them into one English insight feed with language tags and sentiment. That is literally the global media-monitoring / compliance / "ingest the world's audio, get unified insight" workflow enterprises budget for. The Microsoft-tier buyers recognize it instantly. The VCs see throughput (30 clips to a brief in ~60s). The engineers see the parallel fan-out.

And it acts out the RocketRide tagline. "Any model, any tool, no vendor lock-in" stops being a slogan the moment Charlie swaps `llm_anthropic` to `llm_openai` in one config block, live, and the same Whisper model server keeps running underneath. That swap is the closer, kept distinct from the parallelism story so the two claims don't compete.

**Why this over a plain English fan-reaction wall:** the monolingual wall collapses to "captions appeared." Polyglot Cup adds the one capability that is differentiated, defensible, and timely-only-in-2026 (transcribe-and-translate fan-out across nations) on top of the same crowd-pleasing content. Same virality, plus a moat.

**Lessons absorbed from the winning "Sponsor Wall" concept** (apply these even though our payload differs):
- Drive the grid cascade off **real engine event frames** (`on_sse` / event frames `{lane,text}`), never a timed render. A skeptic can verify it live.
- Make **clickthrough-to-source** the credibility move: every grid tile links back to its clip and the exact transcript span. Refusing to assert anything unsourced IS the selling point.
- **Accuracy = governance:** instruct the LLM to emit `language: unclear` and leave the moment line empty rather than hallucinate when audio is too noisy to be sure. An abstaining demo beats a confidently-wrong one in front of this crowd.
- The enterprise pivot one-liner lands the "so what": "Same pipeline does 500 support calls in 12 languages, or earnings-call risk moments. The clips are the fun part; the harness is the product."

---

## 2. The 30-60 second booth script (second-by-second)

**Pre-state (before any attendee walks up):** the dropper browser page (variant A) OR the SSE grid page (variant B) is already open full-screen on the booth monitor, large tiles. The pipeline has already been started once with `ttl=0` and pre-warmed with 1-2 throwaway clips (Whisper cold start already paid). A folder of ~30 pre-staged clips sits on the desktop ready to drag.

| Time | Operator action | What the attendee sees | Charlie says |
|---|---|---|---|
| 0:00 | Tap a key / grab attention. | Grid of ~30 greyed clip thumbnails (Merlin the duck, Norway escalator, German fans at Buffalo Wild Wings, Brazil, Japan), each labeled with a flag/language. | "The World Cup's happening right now. Here are thirty real fan clips from this week, every language. One cloud pipeline. Watch." |
| 0:05 | Drag the one folder of ~30 clips onto the dropper page (variant A), or hit the run key that fires `send_files()` (variant B). | Every tile flips to a pulsing 'transcribing' state at once. | "It's transcribing all thirty at once, each in its own language." |
| 0:12 | Point at tiles as native-language transcripts land. | Tiles pop into color in a cascade as transcripts stream in: Spanish text, Norwegian text, German text appear in the tiles. | "That's Spanish, that's Norwegian, that's the duck guy in Mexico." |
| 0:25 | Point at the insight column filling. | Each tile flips from native transcript to an English translation + a one-line tagged moment + language tag + sentiment. | "Now every clip is translated to English and tagged with the funniest moment. Thirty clips, five-plus languages, one searchable English feed, in about a minute." |
| 0:40 | Click one tile. | Tile expands to show the source clip + the exact transcript span it was drawn from. | "Every row clicks back to its clip and the exact transcript span. For your compliance team." |
| 0:48 | Cursor on the single token `llm_anthropic` in the config; change to `llm_openai`. Re-run one clip. | The analysis re-colors / re-renders for that clip. | "Same pipeline. Different AI company. I didn't touch the plumbing. That's the harness." |
| 0:55 | Hold the moment. | Attendee leans in. | "Same pipeline does five hundred support calls in twelve languages, or earnings-call risk moments. The clips are the fun part. The harness is the product." |

**The one-liner if you only get one sentence:** "Thirty fan clips, every nation's language, become one English insight feed in a minute, on the same pipeline that'll run your support calls or your earnings transcripts, on any model you want."

**Honest framing rules (say these, they make the rest credible):**
- "Orchestrated fan-out across a shared, warm model," NOT "30 GPUs."
- Never "paste a YouTube link" — there is no YouTube node; clips are pre-staged on purpose. "These are this week's clips, pre-staged; the model swap is what's live."

---

## 3. The .pipe design

**Verified shape (matches `pipelines/polyglot.pipe`):** `dropper`/`webhook` (source) -> `parse` (tags -> audio,video) -> `audio_transcribe` (audio+video -> text) -> `question` (text -> questions) -> `prompt` (questions -> questions, injects the instruction) -> `llm_anthropic` (questions -> answers) -> `response_answers` (terminal).

**Lane verification (all confirmed against live services.json):**
- `dropper`/`webhook` source: `_source -> tags` (webhook can also emit audio/video/text/image directly by content-type)
- `parse` (protocol `parse://`, classType `data`): `tags -> [text, table, image, video, audio]`
- `audio_transcribe` (protocol `audio_transcribe://`, classType `audio`): `audio -> text` AND `video -> text`
- `question` (protocol `question://`, classType `text`): `text -> questions`. This is the required bridge: it turns the transcript text into a `questions` record that `prompt`/`llm` can consume.
- `prompt` (protocol `prompt://`, classType `text`): catalog lanes are `{documents:[], questions:["questions"], table:[], text:[]}`. **Only the `questions` input emits anything** (`text`, `documents`, `table` all map to `[]`). So feed `prompt` from the `question` node's `questions` output, NOT from `audio_transcribe`'s `text` directly.
- `llm_anthropic`: `questions -> answers`, capability invoke
- `response_text` (`response_text://`) / `response_answers` (`response_answers://`): terminals. Both exist (plus `response_table`, `response_documents`, etc.).

**CRITICAL config correction (was inverted):** the audio_transcribe Whisper-size key is **`model`** (tiny/base/small/medium/large-v3), default `base`, NOT `mode`. Grounded in the live driver: `audio_transcribe/IGlobal.py:105` reads `config.get('model', 'base')`. The node's internal `preconfig.profiles` block uses `mode`, but the driver never reads it; a `mode` key in your pipe is silently ignored. The default profile buffers `min_seconds: 240` / `max_seconds: 300`; for sub-minute clips the whole clip is one chunk flushed on stream end, so no tuning is strictly required, but you may set lower bounds if a short clip ever stalls. Set `vad_level: 1` (skips minor background noise, good for crowd audio). No API key needed for transcription on cloud (routes to the GPU model server).

**CRITICAL language gap (open risk, must decide before going live):** the driver reads `config.get('language', 'en')` (`IGlobal.py:106`) and passes it straight to Whisper. **There is no auto-detect path: an unset `language` forces English.** The validated `pipelines/polyglot.pipe` currently sets NO `language`, so as written it would transcribe every clip as English, breaking the multilingual core. Fix before the event by either (a) **grouping clips by language and running one pipe per language with `language` set per bucket** (es/pt/de/fr/ja/no), which is the recommended, most-accurate, and most on-message path (it IS the polyglot story); or (b) testing whether `"language": ""`/`null` flows through to Whisper as auto-detect on the live cloud engine (unverified, riskier). For the dropper booth, (a) means dropping one language's folder at a time into its own pre-warmed pipe, or having per-language pipes ready.

**Polyglot language handling:** pre-set `language` per clip batch (es/pt/de/fr/no) rather than trusting auto-detect on short noisy crowd audio. Practically: either (a) run one pipeline with `language` omitted to let Whisper auto-detect (simplest, riskier on noise), or (b) group clips by language and set `language` per batch. Recommend (b) for reliability: it's the polyglot story AND it's more accurate. The LLM also names the language in its output as a cross-check.

### Skeleton A — BOOTH (dropper UI, zero client code) — primary

This is a readable mirror of the validated `pipelines/polyglot.pipe` (the `.pipe` also carries `ui`/position blocks; those are cosmetic). Note the `question` node between transcribe and prompt, and `model` (not `mode`):

```json
{
  "components": [
    { "id": "dropper_1", "provider": "dropper",
      "config": { "hideForm": true, "mode": "Source", "parameters": {}, "type": "dropper" } },
    { "id": "parse_1", "provider": "parse", "config": { "parameters": {} },
      "input": [{ "lane": "tags", "from": "dropper_1" }] },
    { "id": "audio_transcribe_1", "provider": "audio_transcribe",
      "config": { "profile": "default", "default": {
        "model": "base", "language": "es", "vad_level": 1,
        "silence_threshold": 0.25, "min_seconds": 240, "max_seconds": 300
      }, "parameters": {} },
      "input": [{ "lane": "video", "from": "parse_1" }, { "lane": "audio", "from": "parse_1" }] },
    { "id": "question_1", "provider": "question",
      "config": { "type": "question", "parameters": {} },
      "input": [{ "lane": "text", "from": "audio_transcribe_1" }] },
    { "id": "prompt_1", "provider": "prompt",
      "config": { "instructions": [
        "You are given the raw transcript of a short World Cup fan clip in its original language. 1) Name the source language. 2) Translate the transcript to natural English. 3) Give the single most exciting or funniest moment in one short line. If the audio is too unclear to be sure of the language, set the language to 'unclear' and leave the moment empty. Do not invent anything that is not present in the transcript."
      ], "parameters": {} },
      "input": [{ "lane": "questions", "from": "question_1" }] },
    { "id": "llm_anthropic_1", "provider": "llm_anthropic",
      "config": { "profile": "claude-sonnet-4-6", "claude-sonnet-4-6": { "apikey": "${ROCKETRIDE_ANTHROPIC_KEY}" }, "parameters": {} },
      "input": [{ "lane": "questions", "from": "prompt_1" }] },
    { "id": "response_answers_1", "provider": "response_answers", "config": { "laneName": "answers" },
      "input": [{ "lane": "answers", "from": "llm_anthropic_1" }] }
  ],
  "name": "Polyglot Cup",
  "source": "dropper_1",
  "project_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "version": 1
}
```

Notes: (1) `language` is shown as `es` for illustration; per the language gap above, set it per clip bucket (or run a pipe per language). (2) `prompt`'s `instructions` array sits at config top level (not under a profile), matching the validated pipe. (3) the validated pipe uses `claude-sonnet-4-6`; `claude-haiku-4-5` is a faster/cheaper booth alternative if 30-clip latency bites (swap the `profile` and the matching profile key).

Run: `client.use(filepath='polyglot.pipe', ttl=0, use_existing=True)` once -> open the dropper URL printed to the Project Log -> drag the pre-staged clips in. The dropper renders results in its own browser across JSON/text/table/image tabs. This is the most legible 30-second walk-up and needs no client code.

### Skeleton B — SCRIPTED PARALLEL (webhook + send_files, custom grid via SSE) — for the cascade visual

Identical graph, swap `dropper_1` for `webhook_1`:

```json
{ "id": "webhook_1", "provider": "webhook",
  "config": { "hideForm": true, "mode": "Source", "parameters": {}, "type": "webhook" } }
```

Driver (parallel fan of 30 clips, drives the grid off real events):

```python
result = await client.use(filepath='polyglot.pipe', ttl=0, use_existing=True,
                          pipelineTraceLevel='summary')
token = result['token']
files = [ ...30 local clip paths... ]
# uploads all in parallel (default concurrency 64); each file becomes a record
# streaming the same graph. Pass on_sse to render tiles as transcripts/answers land.
results = await client.send_files(files, token, on_sse=on_event)
```

**Downstream insight choice — note for the build:** `prompt -> llm_anthropic -> response_answers` is the cleanest path for our "translate + tag moment" payload (free-form per-clip insight). If you instead want the structured ledger look the winning concept used (BRAND/SENTIMENT/QUOTE/CLIP columns), use `extract_data` (text -> answers,documents; control: llm) -> `response_table` and instruct it to emit language/translation/moment/sentiment columns. extract_data is verified (text -> answers,documents). For Polyglot specifically, stick with the validated `question -> prompt -> llm` path for the translation framing; keep extract_data->response_table as the alternate if a tabular grid reads better on the booth screen. Note the graph already routes the transcript through a `question` node (the required `text -> questions` bridge) before `prompt`; if `prompt`'s instruction handling turns out unreliable on the live engine, drop `prompt` and move the instruction into the llm config / system prompt, feeding the llm straight from `question_1`.

**Control plane:** in this graph the LLM is a normal data-lane node (`questions -> answers`), so NO `control` array is needed. The `control` edge is only required for `summarization` / `extract_data` / agents, which consume an LLM as a helper (`control: [{classType:"llm", from:"llm_1"}]`). If you switch the downstream to `extract_data`, add that control edge and remove the `questions` input on the LLM.

---

## 4. Data prep

**Hard constraint (R2, verified):** there is NO YouTube node, NO URL/video-download node, NO web-fetch source node in RocketRide. `tool_apify`/`tool_firecrawl`/`tool_http_request` are agent tools (classType tool, no data lanes), not pipeline sources. So clips MUST be pre-downloaded to local files. This is the #1 de-risk item. Also: `filesys://` source is `nosaas`/`noremote` — it CANNOT run on cloud. Do not author it.

**How files enter the cloud pipeline (3 verified source nodes):**
1. `dropper` — best for booth. Browser drag-and-drop UI, URL+key printed to Project Log on start, renders results in-browser. Zero client code. (Skeleton A)
2. `webhook` — programmatic, driven by `client.send_files(files, token)` which uploads many files in parallel (default concurrency 64). (Skeleton B)
3. `chat` — questions only, not for files.

**Clip set: ~30 clips, fan/creator UGC only (rights-safe), grouped by language.** NOT FIFA broadcast / FOX / Telemundo / highlight rips (FIFA Content-ID enforces those, even on fan-shot celebration clips). Fan/creator reaction content is both lower-risk and more visually compelling (faces and crowds, not pitch action). Treat as transient internal demo footage; do not redistribute or record-and-publish the booth screen.

Suggested mix (confirmed-viral, sub-minute, multilingual):
- **Spanish (es):** Mexico fan clips incl. Merlin-the-duck-in-a-jersey reactions; Spanish-speaking fan commentary.
- **German (de):** Freddy & Fiago at Buffalo Wild Wings (2.7M views).
- **Norwegian (no):** Norway fans rowing imaginary boats up the escalator.
- **Portuguese (pt):** Brazil fan reactions.
- **Japanese (ja):** Japan fan clips.
- **French (fr):** Canada-match fan reactions.
- Pad to ~30 with first-US-food reaction clips and fan-reaction compilations.

Aim for ~5-6 clips per language across 5-6 languages = 30. Curate toward the cleanest audio you can find per language; one wrong/garbled language tag is visible and embarrassing.

**Pre-download steps (do this well before doors):**
1. `yt-dlp` each clip to mp4 (or extract audio to mp3/wav). Keep them under ~1 minute.
2. Sort into per-language subfolders so you can run/label by `language` batch.
3. Sanity-check audio is intelligible; drop garbled ones.
4. Pre-test the EXACT clips through the live cloud pipeline (transcription + translation) and fix any that mis-transcribe before the event. Pre-testing the actual clip set is non-negotiable.

---

## 5. How parallelism is achieved and verified

**Be honest on stage — two distinct facts, only one documented for the multi-clip case:**

**DOCUMENTED + RELIABLE (use this):** The engine spawns an independent execution context per incoming task and concurrent requests to the same pipeline don't queue behind each other. The bulletproof pattern: `client.use()` ONCE, then `client.send_files([...30...], token)` uploads all clips in parallel (default concurrency 64); each file becomes a record streaming the same graph. The engine streams records across threads and runs independent branches concurrently.

**THE HONEST BOTTLENECK:** transcription runs on ONE shared Whisper model on the GPU model server, serialized through a global lock (confirmed in transcribe.py / README: a single loaded model shared safely across instances). So 30 clips pipeline through but the GPU step is effectively serialized. With `model: "base"` on sub-minute clips each transcription is fast, so 30 still finishes quickly, but it is NOT 30x wall-clock on the GPU. **Frame it as "fan-out orchestration with a shared warm model," never "30 GPUs."**

**Do NOT claim** that dropping 30 files into one token spawns 30 concurrent transcribe workers — per-record worker concurrency is undocumented. Rely on the send_files parallel-upload pattern for the visible parallelism story.

**Verification (so a skeptic can check it live):**
- `client.use(..., pipelineTraceLevel='summary')` emits a `_trace` of every lane write + invoke. Show it.
- Drive the grid cascade off real `on_sse` / engine event frames (`{lane, text}`), never a timed animation. Tiles light up because data actually arrived.
- The monitor stream shows lifecycle events for the production-readiness flex.

---

## 6. Cloud de-risking

**Warm-up (pays the cold start):** cloud reloads models per run; Whisper downloads from HuggingFace on first use then is cached and shared via a global lock. Object-detection-class cold start was ~20s on cloud; budget similar for the first transcription. So: start the pipeline (`use`, `ttl=0`) and push 1-2 throwaway clips through BEFORE doors open, so the Whisper model is loaded and warm.

**Idle death:** cloud pipelines die after ~15 min idle unless `ttl` is set. **Set `ttl=0` in `.use()` (no timeout)** so the warmed pipeline survives booth lulls. Start it ONCE with `use_existing=True` to reuse; do NOT use/terminate per attendee (`use()` is expensive).

**Never block the async event loop** (the #1 runtime failure, bites specifically after 30-60s idle = exactly a booth scenario): no `input()`, `time.sleep`, sync `requests.get`, `readFileSync` in the async flow — they freeze the websocket keepalive and the connection drops (~60s) with "Connection closed." Use `asyncio.sleep` / `run_in_executor`.

**Submitted != succeeded:** `use()` only STARTS the pipeline. The push call (send_files/chat) returns the result inline; poll `get_task_status` to a terminal state (5=COMPLETED, 6=CANCELLED) for long work before claiming a result. `await asyncio.sleep(1)` between polls.

**Validate is mandatory and cheap:** `validate()` MUST return 0 errors before any run. Missing required config (e.g. no apikey) is a validation failure.

**Graded fallback ladder (have all three ready):**
1. **Primary:** polished SSE grid (Skeleton B) cascading off real events.
2. **Fallback 1:** native `dropper` browser tabs (Skeleton A) — same pipeline, zero client code, renders results itself. If your custom grid UI flakes, switch to this.
3. **Fallback 2:** a **pre-recorded screen capture** of a clean full run (transcribe -> translate -> tag -> model swap). If the noisy-booth network flaps or cloud stalls, play the recording. Record this in advance regardless.

**Pre-record specifically:** one clean end-to-end run including the `llm_anthropic` -> `llm_openai` swap, so the closer is safe even on a bad network.

---

## 7. Talking points by attendee type

**AI engineers / researchers:**
- One DAG, typed lanes, streaming execution: records flow through independent branches concurrently across threads.
- Fan-out via `send_files` (parallel upload, concurrency 64) into one pipeline token; honest bottleneck is the shared warm Whisper model behind a global lock, not 30 GPUs.
- `pipelineTraceLevel='summary'` gives a `_trace` of every lane write/invoke — verifiable, not a timed render.
- Whisper on the cloud GPU model server, no API key; swap the LLM provider in one config block.

**Investors / VCs:**
- Throughput story: 30 clips, 5+ languages, to one English insight feed in ~60s. The transcript-to-insight / "find the key moment in hours of video" workflow is a named enterprise category (media, legal, research).
- "Any model, any tool, no lock-in" is a real moat against single-vendor AI stacks — demonstrated live by the one-line model swap.
- 2026 is the year of ROI: this is production-grade orchestration with observability, not a capability flex.

**Enterprise buyers (Microsoft-tier):**
- This is global media-monitoring / compliance / multilingual ingestion: ingest the world's audio, get unified English insight with source attribution.
- Governance: every row clicks through to source clip + exact transcript span; the model abstains (`language: unclear`, empty moment) rather than assert anything unsourced. Refusing to hallucinate is the feature.
- Same pipeline runs 500 support calls in 12 languages or earnings-call risk moments. Self-host and cloud run the IDENTICAL `.pipe`; only endpoint/auth differ. No lock-in at the infra layer either.

---

## 8. Build checklist + open questions

**Build checklist:**
- [ ] Pre-download ~30 rights-safe fan/creator UGC clips via yt-dlp, sorted into per-language subfolders; drop garbled audio.
- [x] Author `polyglot.pipe` (validated 1/1); uses `model: "base"`, `vad_level: 1`. **TODO: set per-language `language` (no auto-detect; unset = forced English).**
- [ ] `validate()` the pipe against the LIVE cloud engine -> must return 0 errors.
- [ ] Set `ROCKETRIDE_ANTHROPIC_KEY` (and `ROCKETRIDE_OPENAI_KEY` for the swap) as env vars; use `${...}` refs in the pipe, never literals.
- [ ] Confirm `ROCKETRIDE_URI=https://api.rocketride.ai` + auth token; https/wss only.
- [ ] Build the SSE grid UI (Skeleton B) driven by real `on_sse`/event frames; OR rehearse the dropper-tabs path (Skeleton A).
- [ ] Pre-test the EXACT 30 clips end-to-end on cloud; fix mis-transcriptions / wrong language tags.
- [ ] Pre-record one clean full run including the model swap.
- [ ] Booth runbook: start pipeline once with `ttl=0, use_existing=True`; warm with 1-2 throwaway clips before doors; never per-attendee use/terminate.
- [ ] Rehearse the 60s script + the honest framing lines until automatic.

**Open questions to verify against the live cloud before the event (do not assume):**
1. **Response node variant:** does the live engine expose lane-specific `response_answers`/`response_text` (confirmed in source) or a single `response` with `config.laneName`? Use whatever `get_services()`/`validate()` confirms; if you customize `laneName`, your client must read that exact key.
2. **`prompt` instruction config shape (resolved in the validated pipe):** `prompt` takes an `instructions` array at config top level (NOT under a profile), and is fed from the `question` node's `questions` output. Still worth a live smoke-test that the instruction actually shapes the LLM output as intended; if not, drop `prompt` and put the instruction in the llm system prompt, feeding the llm straight from `question_1`.
3. **Whisper non-English latency:** verify the cloud Whisper model server transcribes es/pt/de/fr/no at acceptable booth latency with `model: "base"`. Bump to `small` only if accuracy demands it and you've pre-warmed.
4. **Short-clip flush:** confirm sub-minute clips flush promptly with default `min_seconds: 240`/`max_seconds: 300` (they should, via end-of-stream flush). If any clip stalls, lower min/max_seconds.
5. **send_files concurrency on cloud:** confirm parallel upload (concurrency 64) actually holds on the cloud endpoint, not just self-host, and the cascade renders progressively.
6. **`llm_openai` profile name:** confirm the exact profile/model id for the swap (e.g. the live catalog's OpenAI profile key) so the one-line swap actually validates.
7. **dropper URL exposure:** confirm the dropper's public URL/auth key prints to the Project Log on cloud and is reachable from the booth network.

**Verified-against-source facts you can build on without re-checking:** audio_transcribe config key is **`model`** (NOT `mode`; driver reads `config.get('model','base')` at IGlobal.py:105); audio_transcribe lanes audio/video -> text; `language` defaults to `en` with no auto-detect (IGlobal.py:106), so set it per language bucket; parse (parse://, data) tags -> [text,table,image,video,audio]; **`question` (text -> questions)** is the required bridge into `prompt`; `prompt` emits ONLY from its `questions` input (`text`/`documents`/`table` lanes are all `[]`); llm_anthropic questions -> answers; extract_data text -> answers,documents; response_answers exists (terminal, `answers -> []`); no YouTube/URL/filesys-on-cloud ingest.