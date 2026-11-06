#!/usr/bin/env python3
"""A151 still-image video render gate. Requires 40+ distinct, visually APPROVED shots.
Usage:
  python scripts/render_a151_video.py --plan episodes/A151/v3/scene-plan.json \
    --shots-dir /path/to/episode-assets --audio /path/to/A151.mp3 \
    --srt episodes/A151/inputs/subtitles-latest.srt \
    --qa /path/to/episode-assets/visual-qa.json --output /path/to/A151_final.mp4
visual-qa.json: {"approved_shots":["A151-S001",...],"reviewer":"...","notes":"..."}
This script is not an image generator or a substitute for human inspection.
"""
import argparse, hashlib, json, shutil, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageOps

def run(command, cwd=None):
    proc=subprocess.run(command,cwd=cwd,check=False,capture_output=True,text=True)
    if proc.returncode:
        raise RuntimeError(f"{' '.join(map(str,command[:6]))}: {proc.stderr[-2500:]}")
    return proc.stdout

def duration(path):
    obj=json.loads(run(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(path)]))
    return float(obj["format"]["duration"])

def stamp(s):
    h,m,t=s.replace(",",".").split(":")
    return int(h)*3600+int(m)*60+float(t)

def last_subtitle_end(srt):
    import re
    ends=re.findall(r"-->\s*(\d\d:\d\d:\d\d[,.]\d\d\d)",srt)
    if not ends: raise ValueError("No SRT timecodes")
    return stamp(ends[-1])

def phash(img):
    g=ImageOps.grayscale(img).resize((9,8),Image.Resampling.LANCZOS)
    p=list(g.getdata());v=0
    for y in range(8):
        for x in range(8):
            v=(v<<1)|(p[y*9+x]>p[y*9+x+1])
    return v

def main():
    ap=argparse.ArgumentParser()
    for flag in ("plan","shots-dir","audio","srt","qa","output"):
        ap.add_argument("--"+flag,required=True,type=Path)
    args=ap.parse_args()
    plan=json.loads(args.plan.read_text(encoding="utf-8"))
    shots=plan["shots"]
    if len(shots)<40: raise ValueError("Need at least 40 independent story shots")
    approved=json.loads(args.qa.read_text(encoding="utf-8"))
    approved_ids=set(approved.get("approved_shots",[]))
    if not approved.get("reviewer") or not approved.get("notes"):
        raise ValueError("Visual QA requires reviewer and notes")
    missing_approval=[s["id"] for s in shots if s["id"] not in approved_ids]
    if missing_approval:raise ValueError("Not visually approved: "+",".join(missing_approval))
    if not args.audio.is_file() or not args.srt.is_file():raise FileNotFoundError("Audio and SRT both required")
    d=duration(args.audio)
    sub_text=args.srt.read_text(encoding="utf-8-sig")
    sub_end=last_subtitle_end(sub_text)
    if abs(d-sub_end)>1.5:raise ValueError(f"Audio {d:.3f}s, SRT {sub_end:.3f}s out of sync")
    if abs(float(shots[0]["start"]))>.03:raise ValueError("First shot must start at 0")
    for left,right in zip(shots,shots[1:]):
        if abs(float(left["end"])-float(right["start"]))>.05:raise ValueError("Timeline gap/overlap between shots")
    if abs(float(shots[-1]["end"])-sub_end)>0.1:raise ValueError("Shot timeline does not align with final subtitle")
    digest=set(); fingerprints=[]
    paths=[]
    for s in shots:
        loc=args.shots_dir/s["output_image"]
        if not loc.is_file(): raise FileNotFoundError(f"Missing real independent image: {loc}")
        bs=loc.read_bytes();digestval=hashlib.sha256(bs).hexdigest()
        if digestval in digest:raise ValueError(f"Repeated identical image in {s['id']}")
        digest.add(digestval)
        with Image.open(loc) as inp:im=inp.convert("RGB")
        if min(im.size)<720:raise ValueError(f"Too small: {loc}")
        p=phash(im)
        if any((p^old).bit_count()<=3 for old in fingerprints):
            raise ValueError(f"Visually near-duplicate image: {loc}")
        fingerprints.append(p);paths.append(im)
    if len(digest)<40:raise ValueError("Fewer than 40 distinct images")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):raise RuntimeError("ffmpeg / ffprobe required")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="a151-") as t:
        temp=Path(t);frames=temp/"frames";frames.mkdir()
        concat=["ffconcat version 1.0"]
        for index,(s,image) in enumerate(zip(shots,paths)):
            frame=ImageOps.fit(image,(1280,720),method=Image.Resampling.LANCZOS,centering=(0.5,0.5))
            framepath=frames/f"{index:03}.png";frame.save(framepath)
            diff=float(s["end"])-float(s["start"])
            if index==len(shots)-1:diff+=max(0,d-sub_end)
            if diff<=0:raise ValueError(f"Invalid shot duration {s['id']}")
            concat.extend([f"file 'frames/{index:03}.png'",f"duration {diff:.4f}"])
        concat.append(f"file 'frames/{len(shots)-1:03}.png'")
        (temp/"frames.ffconcat").write_text("\n".join(concat)+"\n",encoding="utf-8")
        (temp/"subtitle.srt").write_text(sub_text,encoding="utf-8")
        vf=("fps=24,scale=1280:720,format=yuv420p,"
            "subtitles=subtitle.srt:force_style="
            "'FontName=Noto Sans CJK SC,FontSize=22,Alignment=2,"
            "MarginV=36,Outline=1.5,Shadow=0.5,PrimaryColour=&H00FFFFFF'")
        cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
             "-f","concat","-safe","0","-i","frames.ffconcat",
             "-i",str(args.audio.resolve()),"-map","0:v:0","-map","1:a:0",
             "-vf",vf,"-c:v","libx264","-preset","medium","-crf","19",
             "-pix_fmt","yuv420p","-r","24","-c:a","aac","-b:a","192k",
             "-t",f"{d:.3f}","-movflags","+faststart",str(args.output.resolve())]
        run(cmd,cwd=temp)
    video_length=duration(args.output)
    if abs(video_length-d)>0.5:raise RuntimeError(f"Render duration mismatch {video_length} vs {d}")
    meta={"episode":plan.get("episode"),"output":str(args.output),"duration":video_length,
          "audio_duration":d,"subtitle_end":sub_end,"shot_count":len(shots),
          "distinct_source_shas":len(digest),"visual_qa":str(args.qa),
          "camera":"STATIC, hard-cuts; no synthetic shake or pan",
          "result":"RENDERED_WAITING_FOR_END_TO_END_WATCH_REVIEW"}
    args.output.with_suffix(".render-report.json").write_text(
        json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(meta,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
