# Video Translator

A RocketRide pipeline that takes a short video or audio clip in any language, transcribes it with Whisper (automatic language detection), then uses an LLM to translate it to English and tag the key moment. One pipeline handles every language; there is no per-language configuration.

## Pipeline

```
dropper -> parse -> audio_transcribe -> question -> prompt -> llm_openai -> response_answers
```

- `pipelines/video-translator.pipe` is the single pipeline.
- `audio_transcribe` (Whisper) auto-detects the spoken language: the `language` field is left unset.
- The LLM (GPT, via `llm_openai`) names the source language, translates the transcript to English, and tags the key moment. It is instructed to abstain (language "unclear", empty moment) rather than guess when the audio is too unclear to read.

## Run

```bash
python3 tools/validate_pipes.py .     # expect: VALID: 1/1
cp .env.example .env                   # fill in ROCKETRIDE_OPENAI_KEY
```

Then run the pipeline in the RocketRide IDE (local engine): open `pipelines/video-translator.pipe`, open the dropper URL from the Project Log, and drop a video or audio file in. `tools/connection_check.py` confirms the local engine is reachable.

## Output

Three lines per clip:

1. Source language (named in English)
2. English translation of the transcript
3. Key moment (one short line)

## Roadmap

The longer-term goal is a fuller video translator that returns the same video in two forms: a dubbed version (English audio in a voice similar to the original speaker) and a subbed version (the original audio with burned-in English captions). RocketRide does not yet have the nodes this needs (transcript timestamps, SRT/VTT generation, subtitle burn-in, audio muxing, and voice-cloning TTS), so it is planned as a set of new processor nodes, prototyped outside RocketRide first and ported in once the quality is validated.

## Notes

- Bring your own media: clips are dropped in locally. There is no URL or YouTube ingest node.
- Never hardcode keys in a `.pipe`; use `${ROCKETRIDE_*}` references only. `.env` is gitignored.
- `archive/` holds the original per-language demo pipes and scripts for reference.
