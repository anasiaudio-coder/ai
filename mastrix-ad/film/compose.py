"""Assemble the cinematic film from the Kling clips, the Arabic overlay and the audio stems.

Needs the seven clips in build/film/clips/ (downloaded from the Higgsfield CDN when it is
reachable, or placed there by hand as s1.mp4 ... s7.mp4).

Usage:
  python3 -I film/build_film_audio.py
  node film/render_overlay.mjs
  python3 -I film/compose.py            ->  out/mastrix_film.mp4
"""
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build/film"
CLIPS = Path(os.environ.get("FILM_CLIPS", B / "clips"))
OUT = Path(os.environ.get("FILM_OUT", ROOT / "out/mastrix_film.mp4"))
# Same chain as scripts/normalize.py: tame peaks so linear loudnorm can reach -14 LUFS
PRE = "acompressor=threshold=-26dB:ratio=3:attack=5:release=150:makeup=4,alimiter=limit=0.25:attack=1.5:release=60:level=false"
TARGET = "I=-14:TP=-1.5:LRA=11"


def run(args, **kw):
    return subprocess.run(args, check=True, **kw)


def has_audio(path):
    out = run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
              capture_output=True, text=True).stdout
    return bool(out.strip())


def fetch(plan):
    CLIPS.mkdir(parents=True, exist_ok=True)
    for s in plan["shots"]:
        dst = CLIPS / f"s{s['n']}.mp4"
        if not dst.exists():
            run(["curl", "-fsS", "-o", str(dst), plan["cdn"] + s["file"]])


def main():
    plan = json.loads((ROOT / "film/plan.json").read_text())
    fetch(plan)
    shots, d, fps, total = plan["shots"], plan["dissolve"], plan["fps"], plan["duration"]
    cuts = [s["cut"] for s in shots] + [total]
    lens = [cuts[i + 1] - cuts[i] + (d if i < len(shots) - 1 else 0) for i in range(len(shots))]
    scale = plan["endcard"]["scale"]

    inputs, vf, af, sfx = [], [], [], []
    for i, s in enumerate(shots):
        inputs += ["-i", str(CLIPS / f"s{s['n']}.mp4")]
        base = (f"[{i}:v]trim=start={s['in']}:duration={lens[i]},setpts=PTS-STARTPTS,fps={fps},"
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1")
        if s.get("endcard"):
            # hold the formed logo, and sit it higher with a blurred fill so the name fits below it
            fw, fh = round(1080 * scale / 2) * 2, round(1920 * scale / 2) * 2
            vf.append(f"{base},tpad=stop_mode=clone:stop_duration={lens[i]},trim=duration={lens[i]},split[e1][e2]")
            vf.append("[e1]scale=1296:2304,crop=1080:1920,boxblur=28:2[eb]")
            # feather the inset's edges into the blurred fill so no frame line shows
            vf.append(f"[e2]scale={fw}:{fh},format=yuva420p,"
                      "geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':"
                      "a='255*clip(min(min(X,W-X),min(Y,H-Y))/110,0,1)'[ef]")
            vf.append(f"[eb][ef]overlay=x=(W-w)/2:y=20,format=yuv420p[v{i}]")
        else:
            vf.append(f"{base},format=yuv420p[v{i}]")
        if has_audio(CLIPS / f"s{s['n']}.mp4"):
            ms = int(s["cut"] * 1000)
            af.append(f"[{i}:a]atrim=start={s['in']}:duration={min(lens[i], 5.0)},asetpts=PTS-STARTPTS,"
                      f"afade=t=in:d=0.05,afade=t=out:st={max(0, min(lens[i], 5.0) - 0.35)}:d=0.35,"
                      f"volume=0.5,adelay={ms}|{ms}[a{i}]")
            sfx.append(f"[a{i}]")

    prev = "v0"
    for i in range(1, len(shots)):
        vf.append(f"[{prev}][v{i}]xfade=transition=fade:duration={d}:offset={cuts[i]}[x{i}]")
        prev = f"x{i}"
    n = len(shots)
    inputs += ["-framerate", str(fps), "-i", str(B / "overlay/%04d.png"), "-i", str(B / "vo.wav"), "-i", str(B / "bed.wav")]
    vf.append(f"[{prev}][{n}:v]overlay=0:0,format=yuv420p,trim=duration={total}[vout]")
    if sfx:
        af.append(f"{''.join(sfx)}amix=inputs={len(sfx)}:normalize=0,apad=whole_dur={total}[sfx]")
        af.append(f"[{n + 1}:a]asplit[vo1][vo2]")
        af.append("[sfx][vo2]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[sfxd]")
        af.append(f"[vo1][{n + 2}:a][sfxd]amix=inputs=3:normalize=0,atrim=duration={total}[aout]")
    else:
        af.append(f"[{n + 1}:a][{n + 2}:a]amix=inputs=2:normalize=0,atrim=duration={total}[aout]")

    graph = ";".join(vf + af)
    video, premix = B / "film_video.mp4", B / "film_premix.wav"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph,
         "-map", "[vout]", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-r", str(fps), str(video), "-map", "[aout]", "-ar", "48000", str(premix)])

    err = run(["ffmpeg", "-hide_banner", "-i", str(premix), "-af", f"{PRE},loudnorm={TARGET}:print_format=json", "-f", "null", "-"],
              capture_output=True, text=True).stderr
    m = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    norm = (f"{PRE},loudnorm={TARGET}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
            f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    out = OUT
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(premix), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
         "-af", norm, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest", "-movflags", "+faststart", str(out)])
    print(out)


if __name__ == "__main__":
    main()
