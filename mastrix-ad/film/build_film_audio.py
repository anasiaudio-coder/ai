"""Voice and music stems for the cinematic film, on the variant-A voice timeline.

Writes build/film/vo.wav and build/film/bed.wav (pad + hits). Clip sound effects are mixed
in later by film/compose.py, once the Kling clips are available locally.

Usage: python3 -I film/build_film_audio.py
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_audio as ba  # noqa: E402

OUT = ROOT / "build/film"


def write(path, x):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(ba.SR), "-ac", "1", "-i", "-", str(path)],
                   input=x.astype(np.float32).tobytes(), check=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    plan = json.loads((ROOT / "film/plan.json").read_text())
    duration = plan["duration"]
    cuts = {s["n"]: s["cut"] for s in plan["shots"]}
    lock = plan["endcard"]["lock"]

    src = ba.decode(ba.SRC)
    src = src / (np.abs(src).max() + 1e-9) * 0.7
    hook, body, _ = ba.build_variant("A", src)
    n = int(duration * ba.SR)
    vo = np.zeros(n)
    for seg in hook + body:
        ba.place(vo, ba.cut(src, *seg["src"]), seg["start"] - ba.PAD_IN)
    P = {b["id"]: b for b in body}

    bed = 0.08 * ba.pad(duration, [(0.0, ba.DM9), (cuts[3], ba.BBMAJ7), (cuts[5], ba.F_A), (lock, ba.DMAJ9)])
    hits = np.zeros(n)
    ba.place(hits, ba.sfx_sub_hit(0.5), 0.0)
    for k in (2, 3, 4, 5, 6, 7):
        ba.place(hits, ba.sfx_whoosh(0.5, 0.04), max(0, cuts[k] - 0.4))
    ba.place(hits, ba.sfx_riser(lock - cuts[7] - 0.2, 0.06), cuts[7] + 0.2)
    ba.place(hits, ba.sfx_sub_hit(0.6, 2.0), lock)
    ba.place(hits, ba.sfx_bell([587.33, 739.99, 880.0], 0.09, 1.6, 3.0), lock)
    ba.place(hits, ba.sfx_sub_hit(0.28, 1.2), P["P15"]["start"])

    win = int(0.05 * ba.SR)
    e = np.sqrt(np.convolve(vo ** 2, np.ones(win) / win, mode="same"))
    e = np.convolve(e, np.ones(int(0.25 * ba.SR)) / int(0.25 * ba.SR), mode="same")
    duck = 1.0 - 0.55 * np.clip(e / (e.max() * 0.25 + 1e-9), 0, 1)

    write(OUT / "vo.wav", vo)
    write(OUT / "bed.wav", bed * duck + hits)
    np.save(OUT / "duck.npy", duck.astype(np.float32))
    print("wrote", OUT / "vo.wav", OUT / "bed.wav")


if __name__ == "__main__":
    main()
