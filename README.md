# Polyglot Cup

**One moment, every nation's voice, one English insight feed in 60 seconds.**

A one-minute live booth demo built for **RocketRide Cloud Launch Night** (Shack15, San Francisco, June 18 2026). Drop ~30 short World Cup fan clips in five-plus languages into a single RocketRide cloud pipeline. Whisper transcribes each clip in its native language, an LLM translates every transcript to English and tags the language plus the one funniest or most-exciting moment, and the booth screen fills with one unified insight feed.

The closer: swap `llm_anthropic` to `llm_openai` in one config line, live, while the same Whisper model server keeps running underneath.

---

## The idea

The World Cup is live during the event (June 11 to July 19, hosted USA/Canada/Mexico), so a duck in a Mexico jersey is the single most universally legible thing you can put on a screen at an SF launch night. That buys the first five seconds from everyone walking past.

But this audience (AI engineers, VCs, enterprise buyers) yawns at transcription, and they are right to: speech-to-text is a roughly $4.4B commodity at 95%+ accuracy. So transcription here is invisible plumbing, not the pitch. The pitch is the thing on top that the commodity STT players cannot do in a single pipeline run:

**Multimodal AND multilingual in one shot.** Whisper transcribes each clip in its source language, then one LLM pass unifies all of them into a single English insight feed with language tags and the key moment per clip. That is the global media-monitoring / compliance / "ingest the world's audio, get unified insight" workflow enterprises already budget for. The throughput is the story (30 clips to a brief in about a minute) and the model swap is the moat: "any model, any tool, no vendor lock-in" stops being a slogan the moment the LLM provider changes in one config block, live, and nothing else in the pipeline moves.

The enterprise one-liner that lands the "so what": *the same pipeline runs 500 support calls in 12 languages, or earnings-call risk moments. The clips are the fun part. The harness is the product.*

## How it works

A single RocketRide pipeline (`pipelines/polyglot.pipe`), validated against the live cloud node catalog:

```
dropper -> parse -> audio_transcribe -> question -> prompt -> llm_anthropic -> response_answers
 (source)  (split    (Whisper, native   (text ->   (inject     (translate +      (terminal)
            audio/    language ->        questions  translate-   tag moment)
            video)    text)              bridge)    and-tag
                                                    instruction)
```

| Node | Role |
|---|---|
| `dropper` | Source. Serves its own drag-and-drop browser UI, renders results in-browser, zero client code. Best for a walk-up booth. |
| `parse` | Splits each uploaded clip into `audio` / `video` lanes. |
| `audio_transcribe` | Whisper on the cloud GPU model server (no API key). Transcribes in the clip's native language. |
| `question` | Required bridge: turns the transcript `text` into a `questions` record that `prompt` / `llm` can consume. |
| `prompt` | Injects the translate-and-tag instruction (name the language, translate to English, give the one key moment, abstain if unsure). |
| `llm_anthropic` | The swappable insight step (`questions -> answers`). One config line swaps it to `llm_openai`, etc. |
| `response_answers` | Terminal. Returns the per-clip insight to the UI. |

Two non-obvious facts are baked into the validated pipe (the original plan skeleton had both wrong):

1. The `audio_transcribe` Whisper-size key is **`model`** (`tiny`/`base`/`small`/`medium`/`large-v3`), not `mode`. The live driver reads `config.get('model', 'base')`; a `mode` key is silently ignored.
2. `prompt` only emits from a **`questions`** input (its `text`/`documents`/`table` lanes produce nothing), so the transcript has to pass through a `question` node first.

## Repository layout

| Path | What it is |
|---|---|
| `pipelines/polyglot.pipe` | The validated dropper pipeline. **Source of truth.** |
| `PLAN-polyglot-cup.md` | Full build-ready plan: pipeline design, booth script, data prep, parallelism notes, de-risking, talking points, open questions. |
| `STATE.md` | Project state / handoff. Read this first if you are resuming in a fresh session. |
| `rocketride-launch-demo-debate-log.md` | The six-agent design debate (five concept pitches plus a devil's advocate and verdict) that produced this concept. |
| `tools/validate_pipes.py` | Offline structural validator (checks every `.pipe` against the cloud node catalog). |
| `tools/fetch_clips.sh` | Downloads and sorts fan clips into `clips/<lang>/` via `yt-dlp`. |
| `.rocketride/` | Snapshot of the live cloud node catalog (`services-catalog.json`), per-node schemas, and engine docs. |
| `clips/{es,de,no,pt,ja,fr,pad}/` | Per-language clip download targets (gitignored). |
| `.env.example` | Credential template (copy to `.env`, which is gitignored). |

## Quickstart

**1. Validate the pipe offline (no credentials needed):**

```bash
python3 tools/validate_pipes.py .
# expect: === VALID: 1/1 positive pipes ===
```

**2. Set credentials.** Copy `.env.example` to `.env` and fill in:

```
ROCKETRIDE_APIKEY=...          # from cloud.rocketride.ai -> API Keys -> Create
ROCKETRIDE_ANTHROPIC_KEY=...   # the insight LLM
ROCKETRIDE_OPENAI_KEY=...      # for the live model-swap closer
ROCKETRIDE_URI=https://api.rocketride.ai   # already set
```

Reference keys in the pipe as `${ROCKETRIDE_...}`, never as literals.

**3. Install the client and fetch clips:**

```bash
pip3 install rocketride
tools/fetch_clips.sh        # downloads fan UGC into clips/<lang>/; DRY_RUN=1 to preview
```

Then listen-check every clip and delete garbled, multi-speaker, or wrong-language ones. Target ~5 to 6 clean single-speaker clips per language (~30 total).

**4. Run it.** Start the pipeline once (`client.use(filepath='pipelines/polyglot.pipe', ttl=0, use_existing=True)`), open the dropper URL printed to the Project Log, and drag the pre-staged clips in. Pre-warm with one or two throwaway clips before doors open so Whisper is already loaded.

## Key constraints and gotchas

- **No YouTube / URL / web-ingest node exists.** Clips must be pre-downloaded to local files. `dropper` (drag-drop) or `webhook` + `client.send_files()` (scripted) are the cloud-safe sources; `filesys://` cannot run on cloud.
- **Language is not auto-detected.** The driver reads `config.get('language', 'en')`, so an unset `language` forces English and breaks the multilingual core. Group clips by language and set `language` per bucket (es/pt/de/fr/ja/no). This is also the most accurate path, and it *is* the polyglot story.
- **"Parallel" means orchestration fan-out through one shared, warm Whisper model behind a global lock, not 30 GPUs.** Say it that way on stage. The honest claim is concurrency at the orchestration layer with a shared GPU at the model layer, which is exactly how any production multi-agent stack works.
- **Idle death:** cloud pipelines die after ~15 min idle. Set `ttl=0` and start once with `use_existing=True`; never use/terminate per attendee.
- **Never block the async event loop** (no `input()`, `time.sleep`, sync `requests`): it freezes the websocket keepalive and the connection drops after ~60s, which is exactly a booth lull.
- **Rights:** fan/creator UGC only, never FIFA/FOX/Telemundo broadcast (Content-ID). Treat all clips as transient internal demo footage.

## The honesty rule, which is also the pitch

Accuracy is the governance story. The LLM is instructed to mark the language `unclear` and leave the moment empty when the audio is too noisy to be sure, rather than hallucinate. An abstaining demo beats a confidently-wrong one in front of this crowd, and "refusing to assert anything it cannot source" is the exact posture an enterprise compliance buyer is looking for.

On stage: "orchestrated fan-out across a shared, warm model," never "30 GPUs." And never "paste a YouTube link / happening right now": the clips are pre-staged on purpose. The model swap is what's live.

---

Built on [RocketRide](https://rocketride.ai), an open-source LLM/agent pipeline engine. See `PLAN-polyglot-cup.md` for the full build plan and `rocketride-launch-demo-debate-log.md` for the design rationale.
