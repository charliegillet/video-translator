# Polyglot Cup

A one-minute live booth demo for **RocketRide Cloud Launch Night**. One cloud pipeline transcribes ~30 short World Cup fan clips in their native languages (Whisper), then an LLM translates each to English and tags the funniest moment. Closer: swap `llm_anthropic` to `llm_openai` in one line, live.

## Pipeline

```
dropper -> parse -> audio_transcribe -> question -> prompt -> llm -> response_answers
```

- `pipelines/polyglot.pipe` — Anthropic (default)
- `pipelines/polyglot-openai.pipe` — OpenAI variant, for the live model swap

## Run

```bash
python3 tools/validate_pipes.py .   # expect: VALID: 2/2
cp .env.example .env                 # fill ROCKETRIDE_APIKEY + LLM keys
pip3 install rocketride
tools/fetch_clips.sh                 # download fan clips into clips/<lang>/
```

Start the pipeline once (`client.use(filepath='pipelines/polyglot.pipe', ttl=0, use_existing=True)`), open the dropper URL from the Project Log, drag the clips in.

## Files

- `PLAN-polyglot-cup.md` — full build plan
- `STATE.md` — current status / handoff
- `rocketride-launch-demo-debate-log.md` — design debate
- `CLAUDE.md` — repo automation policy
- `.rocketride/` — cloud node catalog + engine docs

## Notes

- No YouTube/URL ingest: clips must be pre-downloaded.
- Set `language` per clip bucket (no auto-detect; unset = English).
- "Parallel" = fan-out through one shared warm Whisper model, not 30 GPUs.
- Never hardcode keys in a `.pipe`; use `${ROCKETRIDE_*}` refs only.
- Fan/creator UGC only (rights). Treat clips as transient demo footage.
