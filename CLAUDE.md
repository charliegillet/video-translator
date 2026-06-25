# CLAUDE.md

Project instructions for Claude Code working in this repo.

**Video Translator** is a RocketRide pipeline that transcribes a short video or audio clip in any language (Whisper, with automatic language detection), then uses an LLM to translate it to English and tag the key moment. One pipeline (`pipelines/video-translator.pipe`) handles every language. See `README.md` for the overview. RocketRide pipeline guidance lives in `.rocketride/docs/` (read it before editing any `.pipe`).

## Git: auto-commit and push everything

At the end of every task that changes files in this repo, automatically commit and push to GitHub. Do not wait to be asked, and do not ask for confirmation first.

1. `git add -A` (stages all changes; `.gitignore` keeps `.env` and `clips/` out).
2. Commit with a short, factual message describing what changed.
3. `git push` to `origin` on the current branch (`main`).

### Guardrails (always apply)

- **Never commit secrets.** `.env` is gitignored; keep it that way. If a key or credential ever ends up staged, unstage and remove it before committing.
- Never force-add a gitignored path (`git add -f`).
- Before committing a `.pipe` change, run `python3 tools/validate_pipes.py .` and only commit if it reports all pipes valid.
- If `git push` is rejected because the remote moved, `git pull --rebase` then push again.
- Keep commit messages honest about what actually changed. Do not inflate.
