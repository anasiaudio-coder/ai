"""Two-pass EBU R128 loudness normalization of build/mix_<V>.wav to -14 LUFS / -1.5 dBTP.

Usage: python3 -I scripts/normalize.py A B C
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = "I=-14:TP=-1.5:LRA=11"
# Tame the sub hits and bells first so linear gain can reach the target without clipping
PRE = "acompressor=threshold=-26dB:ratio=3:attack=5:release=150:makeup=4,alimiter=limit=0.25:attack=1.5:release=60:level=false"

for v in sys.argv[1:] or ["A", "B", "C"]:
    src, dst = ROOT / f"build/mix_{v}.wav", ROOT / f"build/mix_{v}_norm.wav"
    err = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(src), "-af", f"{PRE},loudnorm={TARGET}:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True).stderr
    m = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    af = (f"{PRE},loudnorm={TARGET}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", af, "-ar", "48000", str(dst)], check=True)
    print(v, "input", m["input_i"], "LUFS ->", dst.name)
