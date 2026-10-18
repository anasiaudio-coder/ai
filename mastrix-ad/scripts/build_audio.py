"""Cut the ElevenLabs take into phrases, assemble one VO per hook variant,
synthesize the sound bed against the same cue times, and write the
timeline JSON the visual renderer reads.

Usage: python3 -I scripts/build_audio.py
"""
import json
import subprocess
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "audio/raw/take1.mp3"
OUT = ROOT / "build"
SR = 48000
DURATION = 30.0

# Phrase boundaries in take1.mp3, measured with
# ffmpeg silencedetect=noise=-38dB:d=0.35
HOOKS = {
    "A": [("اللايكات ما بتدفع إيجار.", 0.00, 1.59)],
    "B": [("دفعت على إعلانات…", 3.69, 4.70), ("وما رنّ ولا تلفون؟", 5.23, 6.26)],
    "C": [("صفحتك حلوة.", 8.46, 9.20), ("بس مين بيشتري؟", 9.86, 10.66)],
}
BODY = [
    ("P1", "أغلب الإعلانات بتجيبلك مشاهدات…", 12.96, 14.87),
    ("P2", "وقليل منها بيجيبلك زباين.", 15.35, 16.78),
    ("P3", "بماستريكس ميديا،", 18.73, 19.76),
    ("P4", "منشتغل على شغلة وحدة:", 20.14, 21.45),
    ("P5", "إعلانات بتتحوّل لمحادثات…", 21.87, 23.65),
    ("P6", "والمحادثات لمبيعات.", 24.12, 25.72),
    ("P7", "كل قرش بنصرفه،", 26.19, 27.20),
    ("P8", "بتشوف وين راح…", 27.59, 28.32),
    ("P9", "وشو جاب.", 28.76, 29.22),
    ("P10", "ومنستقبل عدد محدود من العملاء كل شهر،", 29.64, 32.09),
    ("P11", "عشان كل عميل ياخد حقّه.", 32.45, 34.28),
    ("P12", "ابعتلنا على واتساب،", 34.67, 35.81),
    ("P13", "وخلّينا نحكي بالأرقام.", 36.21, 37.37),
    ("P14", "ماستريكس ميديا.", 37.81, 38.67),
    ("P15", "إعلانات بتبيع.", 39.08, 40.10),
]
PAD_IN, PAD_OUT = 0.05, 0.09
HOOK_INNER_GAP = 0.22
HOOK_TO_BODY_GAP = 0.40
MAX_BODY_GAP = 0.75  # the long pause after P2 is tightened to this


def decode(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR),
         "-f", "f32le", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def cut(src, start, end):
    a = max(0, int((start - PAD_IN) * SR))
    b = min(len(src), int((end + PAD_OUT) * SR))
    seg = src[a:b].copy()
    f = int(0.012 * SR)
    seg[:f] *= np.linspace(0, 1, f)
    seg[-f:] *= np.linspace(1, 0, f)
    return seg


def place(buf, seg, t):
    i = int(round(t * SR))
    if i < 0:
        seg, i = seg[-i:], 0
    seg = seg[: max(0, len(buf) - i)]
    buf[i:i + len(seg)] += seg


def lowpass(x, hz, order=2):
    return sosfilt(butter(order, hz, "low", fs=SR, output="sos"), x)


def bandpass(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)


def env_ad(n, attack, decay):
    t = np.arange(n) / SR
    e = np.where(t < attack, t / max(attack, 1e-4), np.exp(-(t - attack) / decay))
    return e


rng = np.random.default_rng(7)


def sfx_sub_hit(level=0.9, length=1.4):
    n = int(length * SR)
    t = np.arange(n) / SR
    f = 42 + 58 * np.exp(-t / 0.07)
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * env_ad(n, 0.004, 0.42)
    click = lowpass(rng.standard_normal(n), 1800) * env_ad(n, 0.001, 0.02) * 0.35
    return (body + click) * level


def sfx_tick(freq=2093.0, level=0.12):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 1.5 * t)
    return tone * env_ad(n, 0.002, 0.07) * level


def sfx_bell(freqs, level=0.10, decay=0.9, length=2.2):
    n = int(length * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, f in enumerate(freqs):
        for mult, amp in ((1, 1.0), (2.01, 0.32), (3.0, 0.12)):
            out += amp * np.sin(2 * np.pi * f * mult * t) * np.exp(-t / (decay / (1 + 0.4 * k * (mult - 1))))
    out *= env_ad(n, 0.003, 10.0)
    return out / max(1, len(freqs)) * level


def sfx_whoosh(length=0.55, level=0.16):
    n = int(length * SR)
    x = bandpass(rng.standard_normal(n), 300, 4200)
    t = np.linspace(0, 1, n)
    e = np.sin(np.pi * np.clip(t, 0, 1) ** 0.7) ** 2
    return x * e * level


def sfx_riser(length=1.3, level=0.20):
    n = int(length * SR)
    t = np.arange(n) / SR
    f = 180 * (4.5 ** (t / length))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    air = bandpass(rng.standard_normal(n), 900, 7000)
    e = (t / length) ** 2.2
    return (tone + air) * e * level


def pad(duration, sections):
    """sections: list of (start_time, [freqs]) -- chords crossfade at each start."""
    n = int(duration * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    xf = 0.8
    for idx, (start, freqs) in enumerate(sections):
        end = sections[idx + 1][0] if idx + 1 < len(sections) else duration + xf
        gate = np.clip((t - start + xf / 2) / xf, 0, 1) * np.clip((end - t + xf / 2) / xf, 0, 1)
        if not gate.any():
            continue
        chord = np.zeros(n)
        for k, f in enumerate(freqs):
            amp = 1.0 / (1 + 0.35 * k)
            chord += amp * (np.sin(2 * np.pi * (f - 0.12) * t + k) + np.sin(2 * np.pi * (f + 0.12) * t + 2 * k))
        out += chord * gate
    lfo = 0.82 + 0.18 * np.sin(2 * np.pi * 0.11 * t)
    out = lowpass(out * lfo, 1100)
    out *= np.clip(t / 1.0, 0, 1)
    out *= np.clip((duration - t) / 0.6, 0, 1)
    return out / (np.abs(out).max() + 1e-9)


# Chords: tension (D minor 9) -> lift (Bb maj7) -> trust (F/A) -> resolve (D maj9)
DM9 = [73.42, 110.0, 174.61, 220.0, 329.63]
BBMAJ7 = [58.27, 87.31, 146.83, 220.0, 349.23]
F_A = [55.0, 87.31, 130.81, 174.61, 261.63]
DMAJ9 = [73.42, 110.0, 185.0, 220.0, 329.63, 440.0]


def build_variant(name, src):
    t = 0.0
    hook_segs = []
    for i, (text, s, e) in enumerate(HOOKS[name]):
        if i:
            t += HOOK_INNER_GAP
        hook_segs.append({"text": text, "src": (s, e), "start": t, "end": t + (e - s)})
        t += e - s
    t += HOOK_TO_BODY_GAP
    body = []
    prev_end_src = None
    for pid, text, s, e in BODY:
        if prev_end_src is not None:
            t += min(s - prev_end_src, MAX_BODY_GAP)
        body.append({"id": pid, "text": text, "src": (s, e), "start": t, "end": t + (e - s)})
        t += e - s
        prev_end_src = e
    duration = max(DURATION, round(t + 0.9, 2))
    return hook_segs, body, duration


def main():
    OUT.mkdir(exist_ok=True)
    src = decode(SRC)
    src = src / (np.abs(src).max() + 1e-9) * 0.7

    for name in HOOKS:
        hook, body, duration = build_variant(name, src)
        P = {b["id"]: b for b in body}
        n = int(duration * SR)

        vo = np.zeros(n)
        for seg in hook + body:
            place(vo, cut(src, *seg["src"]), seg["start"] - PAD_IN)

        # Cue times shared with the visuals
        cues = {
            "hit": 0.0,
            "customers": [round(P["P2"]["start"] + 0.1 + 0.17 * i, 3) for i in range(5)],
            "pings": [round(P["P5"]["start"] + 0.15 + 0.32 * i, 3) for i in range(5)],
            "checks": [round(P["P6"]["start"] + 0.25 + 0.16 * i, 3) for i in range(5)],
            "mStart": round(P["P12"]["start"] - 0.35, 3),
            "mLock": round(P["P12"]["start"] + 0.85, 3),
            "sweep": round(P["P14"]["start"], 3),
            "tagline": round(P["P15"]["start"], 3),
        }
        card_starts = {
            "problem": P["P1"]["start"], "brand": P["P3"]["start"],
            "convert": P["P5"]["start"], "ledger": P["P7"]["start"],
            "seats": P["P10"]["start"], "end": cues["mStart"],
        }

        bed = np.zeros(n)
        bed += 0.075 * pad(duration, [
            (0.0, DM9), (card_starts["brand"], BBMAJ7),
            (card_starts["ledger"], F_A), (cues["mLock"], DMAJ9)])
        sfx = np.zeros(n)
        place(sfx, sfx_sub_hit(0.55), 0.0)
        place(sfx, sfx_whoosh(0.5, 0.05), 0.02)
        for c in ("problem", "brand", "convert", "ledger", "seats"):
            place(sfx, sfx_whoosh(0.5, 0.05), max(0, card_starts[c] - 0.42))
        for i, ct in enumerate(cues["customers"]):
            place(sfx, sfx_tick(2093 * (1 + 0.06 * i), 0.07), ct)
        for i, ct in enumerate(cues["pings"]):
            place(sfx, sfx_bell([880 * (1.122 ** (i % 3))], 0.05, 0.6), ct)
        for ct in cues["checks"]:
            place(sfx, sfx_tick(1568, 0.05), ct)
        place(sfx, sfx_riser(cues["mLock"] - cues["mStart"], 0.07), cues["mStart"])
        place(sfx, sfx_sub_hit(0.6, 2.0), cues["mLock"])
        place(sfx, sfx_bell([587.33, 739.99, 880.0], 0.10, 1.6, 3.0), cues["mLock"])
        place(sfx, sfx_bell([1174.66, 1479.98], 0.035, 1.2, 2.5), cues["sweep"])
        place(sfx, sfx_sub_hit(0.3, 1.2), cues["tagline"])

        # Duck the pad under the voice
        win = int(0.05 * SR)
        e = np.sqrt(np.convolve(vo ** 2, np.ones(win) / win, mode="same"))
        e = np.convolve(e, np.ones(int(0.25 * SR)) / int(0.25 * SR), mode="same")
        duck = 1.0 - 0.55 * np.clip(e / (e.max() * 0.25 + 1e-9), 0, 1)
        mix = vo + bed * duck + sfx
        mix /= max(1.0, np.abs(mix).max() / 0.95)

        wav = OUT / f"mix_{name}.wav"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1",
             "-i", "-", str(wav)], input=mix.astype(np.float32).tobytes(), check=True)

        strip = lambda s: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items() if k != "src"}
        timeline = {
            "variant": name, "duration": duration, "fps": 30,
            "hook": [strip(s) for s in hook], "phrases": {b["id"]: strip(b) for b in body},
            "cards": {k: round(v, 3) for k, v in card_starts.items()}, "cues": cues,
        }
        (OUT / f"timeline_{name}.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1))
        print(name, "duration", duration, "body ends", round(body[-1]["end"], 2))


if __name__ == "__main__":
    main()
