# Tools

## make_audio.py — recorded audio for the app
Generates `audio/thorsten/*.mp3` and `audio/kerstin/*.mp3` for every text the app speaks (card German + example, lesson vocab, readings). Run it after adding or changing a week file, then commit `audio/`.

```sh
pip install --break-system-packages piper-tts      # ffmpeg must be installed
# get the voice models from the `voices` branch (they're split into <50 MB parts)
git fetch --depth 1 origin voices
mkdir -p /tmp/voices && git --work-tree=/tmp/voices checkout FETCH_HEAD -- .
(cd /tmp/voices && for v in de_DE-thorsten-high de_DE-kerstin-medium; do cat $v.onnx.part-* > $v.onnx; done)
git reset -q        # unstage the branch files from main's index
(cd /tmp/voices && sha256sum -c SHA256SUMS)
python3 tools/make_audio.py --voices /tmp/voices
```
Voices: Piper `de_DE-thorsten-high` and `de_DE-kerstin-medium` (both CC0), from huggingface.co/rhasspy/piper-voices.
File names: FNV-1a 32-bit hash of the cleaned text (UTF-8) + "-" + byte length. Must stay identical to `audioKey()` / `ttsClean()` in index.html.
