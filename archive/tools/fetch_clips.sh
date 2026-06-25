#!/usr/bin/env bash
# fetch_clips.sh -- download + sort short World Cup fan clips into clips/<lang>/
# for the Polyglot Cup booth demo.
#
# Rights: fan/creator UGC only. Transient internal demo footage. Do NOT pull
# FIFA/FOX/Telemundo broadcast or highlight rips (Content-ID). Curate toward one
# clear speaker per clip; stadium roar transcribes to garbage.
#
# Requires: yt-dlp + ffmpeg (both present on this machine).
#
# Usage:
#   tools/fetch_clips.sh                  # download into clips/<lang>/
#   PER_QUERY=3 tools/fetch_clips.sh      # fewer results per search query
#   LANGS="es de" tools/fetch_clips.sh    # only these language buckets
#   DRY_RUN=1 tools/fetch_clips.sh        # list what WOULD download, fetch nothing
#   CLIP_SECONDS=45 tools/fetch_clips.sh  # cap each clip to first N seconds
#
# After it runs: listen-check every clip, delete garbled / wrong-language /
# multi-speaker / stadium-roar ones. Target ~5-6 clean single-speaker clips per
# language (~30 total). Then pre-test the EXACT survivors through the cloud pipe.

set -uo pipefail

# ---- config (override via env) ----
PER_QUERY="${PER_QUERY:-4}"           # results pulled per search query
CLIP_SECONDS="${CLIP_SECONDS:-60}"    # hard-cap each clip to its first N seconds
MAX_DUR="${MAX_DUR:-240}"             # skip source videos longer than this (sec)
DATEAFTER="${DATEAFTER:-now-60days}"  # bias toward recent uploads (WC 2026 era)
LANGS="${LANGS:-es de no pt ja fr pad}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE="$ROOT/tools/.dl-archive.txt" # dedupe across runs

# queries per language bucket: native query(ies) first, English fallback last.
# (bash 3.2 on macOS has no associative arrays, so use a case statement.)
queries_for() {
  case "$1" in
    es)  printf '%s\n' \
           "Merlin pato Mexico Mundial 2026 reaccion" \
           "aficion mexicana Mundial 2026" \
           "Merlin the duck Mexico jersey World Cup" ;;
    de)  printf '%s\n' \
           "deutsche Fans WM 2026 USA Reaktion" \
           "Fiago Freddy Buffalo Wild Wings" \
           "German fans Buffalo Wild Wings World Cup 2026" ;;
    no)  printf '%s\n' \
           "Norge fans rulletrapp robat VM 2026" \
           "Norway fans rowing escalator World Cup Boston" ;;
    pt)  printf '%s\n' \
           "torcida Brasil Copa do Mundo 2026 reacao" \
           "Brazil fans reaction World Cup 2026" ;;
    ja)  printf '%s\n' \
           "日本 サポーター ワールドカップ2026 反応" \
           "Japan fans World Cup 2026 reaction" ;;
    fr)  printf '%s\n' \
           "supporters Coupe du Monde 2026 reaction" \
           "France Canada fans World Cup 2026 reaction" ;;
    pad) printf '%s\n' \
           "World Cup 2026 fans first American food reaction" \
           "World Cup 2026 fan reactions compilation shorts" ;;
    *)   printf '%s\n' "World Cup 2026 fan reaction" ;;
  esac
}

clip_count() {  # count media files in a dir
  find "$1" -type f \( -name '*.mp4' -o -name '*.m4a' -o -name '*.webm' -o -name '*.mkv' \) 2>/dev/null | wc -l | tr -d ' '
}

command -v yt-dlp  >/dev/null || { echo "ERROR: yt-dlp not on PATH"; exit 1; }
command -v ffmpeg  >/dev/null || { echo "ERROR: ffmpeg not on PATH"; exit 1; }
mkdir -p "$ROOT/tools"

for lang in $LANGS; do
  outdir="$ROOT/clips/$lang"
  mkdir -p "$outdir"
  echo "==================  $lang  =================="
  while IFS= read -r q; do
    [ -z "$q" ] && continue
    echo "--- search: $q (top $PER_QUERY) ---"
    args=(
      --no-update
      --no-playlist
      --dateafter "$DATEAFTER"
      --match-filter "duration < $MAX_DUR & !is_live"
      --download-sections "*0-$CLIP_SECONDS"
      --force-keyframes-at-cuts
      -S "res:720,ext:mp4:m4a"
      --merge-output-format mp4
      --restrict-filenames
      --ignore-errors
      -o "$outdir/%(id)s.%(ext)s"
    )
    if [ -n "${DRY_RUN:-}" ]; then
      args+=(--simulate --print "id  %(duration)s s  %(upload_date)s  %(title).70s")
    else
      args+=(--download-archive "$ARCHIVE")
    fi
    yt-dlp "${args[@]}" "ytsearch${PER_QUERY}:${q}" || echo "  (query had errors, continuing)"
  done < <(queries_for "$lang")
  echo ">>> $lang: $(clip_count "$outdir") file(s) in $outdir"
done

echo
echo "==================  SUMMARY  =================="
total=0
for lang in $LANGS; do
  c="$(clip_count "$ROOT/clips/$lang")"
  printf "  %-4s %s\n" "$lang" "$c"
  total=$((total + c))
done
echo "  TOTAL: $total clips"
echo
echo "NEXT: listen-check each clip; delete garbled / multi-speaker / wrong-language ones."
echo "Then group stays by folder -> the pipe sets Whisper 'language' per bucket (es/de/no/pt/ja/fr)."
