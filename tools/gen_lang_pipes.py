#!/usr/bin/env python3
"""Generate one clean OpenAI pipe per language bucket and apply the
English-always translate-and-tag instruction. Fixes review C1 + H1 and the
Arabic-answered-in-Arabic prompt issue the Tester caught.

C1: audio_transcribe has NO auto-detect; a static .pipe carries ONE language,
    so we emit one pipe per language in clips/<lang>/ with `language` set.
H1: strip the stray llm_openai parameters.google:{} copy-paste artifact.
Prompt: force the model to ALWAYS answer in English regardless of source language.

NOTE: the double-answer per clip is a separate, engine-level issue: the `prompt`
node default-forwards its un-enriched input to the LLM (one bare answer) in
addition to the instruction-wrapped one. That is NOT fixable in the .pipe (no
node carries an instruction except `prompt`). Consume answers[-1] (always the
instructed one) or patch the local engine prompt node. See STATE/PLAN.

The anthropic base polyglot.pipe is normalized in place. polyglot-openai.pipe is
left to the IDE (it keeps reopening/clobbering it); polyglot-en.pipe is the clean
English booth pipe instead. Deterministic uuid5 project_ids => idempotent.
Run: python3 tools/gen_lang_pipes.py
"""
import json, copy, uuid, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPES = os.path.join(ROOT, "pipelines")
NS = uuid.uuid5(uuid.NAMESPACE_DNS, "polyglot-cup.charliegillet")

# Whisper codes for the buckets with clips (en included as a clean variant).
LANGS = {"en": "English", "es": "Spanish", "pt": "Portuguese", "de": "German",
         "fr": "French", "ja": "Japanese", "ko": "Korean", "ar": "Arabic"}

INSTRUCTION = (
    "You are given the raw transcript of a short World Cup fan clip in its original "
    "language. ALWAYS write your entire response in English, no matter what language "
    "the transcript is in. Respond with exactly three numbered lines and nothing else: "
    "1) Source language: name the language in English. "
    "2) English translation: translate the transcript into natural English. "
    "3) Moment: the single most exciting or funniest moment in one short English line. "
    "If the audio is too unclear to be sure of the language, set the language to "
    "'unclear' and leave the moment empty. Do not invent anything not in the transcript."
)


def fix(components, lang):
    for c in components:
        if c.get("provider") == "audio_transcribe":
            c["config"].setdefault("default", {})["language"] = lang   # C1
        if c.get("provider") in ("llm_openai", "llm_anthropic"):
            c["config"]["parameters"] = {}                             # H1
        if c.get("provider") == "prompt":
            c["config"]["instructions"] = [INSTRUCTION]                # English-always


# normalize the anthropic base (closer pipe); leave polyglot-openai.pipe to the IDE
ap = json.load(open(os.path.join(PIPES, "polyglot.pipe")))
fix(ap["components"], "en")
json.dump(ap, open(os.path.join(PIPES, "polyglot.pipe"), "w"), indent=2)
print("  normalized polyglot.pipe (anthropic): language=en, English-always prompt")

# template off the openai base; fix() cleans google:{} and sets language per variant
tpl = json.load(open(os.path.join(PIPES, "polyglot-openai.pipe")))
for lang, name in LANGS.items():
    p = copy.deepcopy(tpl)
    fix(p["components"], lang)
    p["project_id"] = str(uuid.uuid5(NS, f"polyglot-{lang}"))
    p["name"] = f"Polyglot Cup ({name})"
    p.pop("docRevision", None)
    json.dump(p, open(os.path.join(PIPES, f"polyglot-{lang}.pipe"), "w"), indent=2)
    print(f"  wrote polyglot-{lang}.pipe  language={lang}  project_id={p['project_id'][:8]}...")

print("done.")
