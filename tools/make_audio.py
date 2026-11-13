#!/usr/bin/env python3
"""Generate mp3 audio for every German text the app can speak.

Usage:  python3 tools/make_audio.py --voices DIR [--only thorsten,kerstin]
DIR must contain de_DE-thorsten-high.onnx(.json) and de_DE-kerstin-medium.onnx(.json)
(rebuild them from the `voices` branch: see tools/README.md).

Files go to audio/<voice>/<key>.mp3. The key must match audioKey() in index.html:
clean the text exactly like TTS.say(), then FNV-1a 32-bit hash of the UTF-8 bytes
in 8 hex digits + "-" + UTF-8 byte length. Existing files are skipped.
"""
import argparse, glob, json, os, re, subprocess, sys, tempfile, wave

VOICES = {"thorsten": "de_DE-thorsten-high", "kerstin": "de_DE-kerstin-medium"}
LENGTH_SCALE = 1.05  # slightly slower than default, for learners

def clean(t):
    t = re.sub(r"…|\.\.\.", " ", str(t))
    t = re.sub(r"\([^)]*\)", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def reading_text(t):  # mirrors the "Read aloud" button in index.html
    t = str(t).replace("**", "")
    return re.sub(r"^[\s–-]+", "", t, flags=re.M)

def key(t):
    b = t.encode("utf-8"); h = 0x811C9DC5
    for x in b:
        h ^= x; h = (h * 0x01000193) & 0xFFFFFFFF
    return "%08x-%d" % (h, len(b))

def texts(root):
    out = set()
    for f in sorted(glob.glob(os.path.join(root, "weeks", "week-*.json"))):
        w = json.load(open(f, encoding="utf-8"))
        for c in w.get("cards", []):
            out.add(clean(c.get("de", ""))); out.add(clean(c.get("example", "")))
        for d in w.get("days", []):
            for s in d.get("sections", []):
                if s.get("type") == "vocab":
                    for v in s.get("words", []): out.add(clean(v.get("de", "")))
                if s.get("type") == "reading": out.add(clean(reading_text(s.get("text", ""))))
    out.discard("")
    return sorted(out)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--voices", required=True); ap.add_argument("--only", default=",".join(VOICES))
    a = ap.parse_args(); root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    from piper import PiperVoice
    from piper.config import SynthesisConfig
    items = texts(root); made = 0
    for short in a.only.split(","):
        model = PiperVoice.load(os.path.join(a.voices, VOICES[short] + ".onnx"))
        outdir = os.path.join(root, "audio", short); os.makedirs(outdir, exist_ok=True)
        for t in items:
            dst = os.path.join(outdir, key(t) + ".mp3")
            if os.path.exists(dst): continue
            with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
                with wave.open(tmp.name, "wb") as wf:
                    model.synthesize_wav(t, wf, syn_config=SynthesisConfig(length_scale=LENGTH_SCALE))
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp.name, "-ac", "1", "-c:a", "libmp3lame", "-b:a", "48k", dst], check=True)
            made += 1
    print(f"{len(items)} texts, {made} new files")

if __name__ == "__main__":
    main()
