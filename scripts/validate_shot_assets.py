#!/usr/bin/env python3
"""Gate real single-shot A151 images before video editing (Pillow required).

Usage:
 python scripts/validate_shot_assets.py --plan episodes/A151/v3/scene-plan.json \
   --asset-root /path/to/A151-assets --report /path/to/A151-assets/readiness.json

This script NEVER generates images, marks human visual approval, or certifies a video.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageStat

def dhash(image):
    pixels=list(ImageOps.grayscale(image).resize((9,8),Image.Resampling.LANCZOS).getdata())
    result=0
    for y in range(8):
        for x in range(8):
            result=(result<<1)|(pixels[y*9+x] > pixels[y*9+x+1])
    return result

def grid_warning(image):
    """Heuristic: sharp straight separators at both 1/3 and 2/3 axes."""
    small=image.convert("RGB").resize((360,204),Image.Resampling.BILINEAR)
    px=small.load()
    def vertical(x):
        return sum(sum(abs(px[x,y][k]-px[x-1,y][k]) for k in range(3))/3 for y in range(0,204,3))/68
    def horizontal(y):
        return sum(sum(abs(px[x,y][k]-px[x,y-1][k]) for k in range(3))/3 for x in range(0,360,3))/120
    v=[vertical(x) for x in (120,240)]
    h=[horizontal(y) for y in (68,136)]
    basex=sorted([vertical(x) for x in (100,110,130,140,220,230,250,260)])[3]
    basey=sorted([horizontal(y) for y in (49,55,81,93,121,150,160,175)])[3]
    if min(v)>max(10,basex*2.4) and min(h)>max(10,basey*2.4):
        return ["suspected_3x3_collage"]
    return []

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--plan",required=True,type=Path)
    parser.add_argument("--asset-root",required=True,type=Path)
    parser.add_argument("--report",default="readiness.json",type=Path)
    args=parser.parse_args()
    plan=json.loads(args.plan.read_text(encoding="utf-8"))
    root=args.asset_root
    results=[]; seen=[]
    for shot in plan["shots"]:
        relative=shot.get("output_image") or shot.get("asset")
        if not relative: raise ValueError(f"Shot {shot['id']} has no output_image/asset")
        path=root/relative
        record={"shot":shot["id"],"asset":relative,"status":"MISSING","warnings":[]}
        if path.is_file():
            try:
                with Image.open(path) as src:
                    im=src.convert("RGB")
                digest=hashlib.sha256(path.read_bytes()).hexdigest()
                record.update(status="PRESENT_UNREVIEWED",size=list(im.size),sha256=digest)
                if im.width<1600 or im.height<900:record["warnings"].append("resolution_too_small")
                if abs(im.width/im.height-16/9)>.04:record["warnings"].append("wrong_aspect")
                record["warnings"].extend(grid_warning(im))
                ph=dhash(im)
                for old in seen:
                    if digest==old["sha"]:record["warnings"].append("exact_duplicate:"+old["id"])
                    elif (ph^old["ph"]).bit_count()<=3:record["warnings"].append("near_duplicate:"+old["id"])
                seen.append({"id":shot["id"],"sha":digest,"ph":ph})
            except Exception as error:
                record.update(status="UNREADABLE",warnings=[str(error)])
        results.append(record)
    present=sum(r["status"]=="PRESENT_UNREVIEWED" for r in results)
    warnings=sum(bool(r["warnings"]) for r in results)
    report={"episode":plan.get("episode"),"planned":len(results),"present_unreviewed":present,
            "missing":sum(r["status"]=="MISSING" for r in results),
            "warning_shots":warnings,
            "human_review_needed":["original 2D abstract cartoon white round face with dot eyes and simplified hair",
                                   "same character outfit/hair/body proportions per text role card",
                                   "full single-frame composition, not collage, UI or player",
                                   "natural scale relative to sofa/bed/desk and physically natural occlusion",
                                   "detailed cinematic China settings, realistic light"],
            "visual_pass_count":0,"video_approved":False,"shots":results}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Present: {present}/{len(results)}; missing: {report['missing']}; warnings: {warnings}; visual review required")
    return 0 if present==len(results) and warnings==0 else 2

if __name__=="__main__":
    raise SystemExit(main())
