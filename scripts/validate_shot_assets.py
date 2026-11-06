#!/usr/bin/env python3
"""Validate distinct A151 scene images before editing. Requires Pillow.
Usage: python scripts/validate_shot_assets.py --plan episodes/A151/v3/scene-plan.json --asset-root /path/to/A151 --report readiness.json
Automated checks are necessary, not sufficient: human visual review is still mandatory.
"""
import argparse, hashlib, json
from pathlib import Path
from PIL import Image, ImageOps

def dhash(im):
    pixels=list(ImageOps.grayscale(im).resize((9, 8), Image.Resampling.LANCZOS).getdata())
    value=0
    for y in range(8):
        for x in range(8):
            value=(value<<1)|(pixels[y*9+x]>pixels[y*9+x+1])
    return value

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--asset-root", required=True)
    ap.add_argument("--report", default="readiness.json")
    args=ap.parse_args()
    plan=json.loads(Path(args.plan).read_text(encoding="utf-8"))
    root=Path(args.asset_root)
    results=[]; seen=[]
    for shot in plan["shots"]:
        loc=root/shot["asset"]
        record={"shot":shot["id"],"asset":shot["asset"],"status":"MISSING","warnings":[]}
        if loc.is_file():
            try:
                with Image.open(loc) as source: image=source.copy()
                sha=hashlib.sha256(loc.read_bytes()).hexdigest()
                record.update(status="PRESENT_UNREVIEWED",size=image.size,sha256=sha)
                if image.width<1600 or image.height<900: record["warnings"].append("too_small")
                if abs(image.width/image.height-16/9)>.035: record["warnings"].append("wrong_aspect")
                dh=dhash(image)
                for old in seen:
                    if sha==old["sha"]: record["warnings"].append("exact_duplicate:"+old["shot"])
                    elif (dh^old["dh"]).bit_count()<=3: record["warnings"].append("near_duplicate:"+old["shot"])
                seen.append({"sha":sha,"dh":dh,"shot":shot["id"]})
            except Exception as error:
                record.update(status="UNREADABLE",warnings=[str(error)])
        results.append(record)
    present=sum(r["status"]=="PRESENT_UNREVIEWED" for r in results)
    report={"episode":plan.get("episode"),"planned":len(results),"present_unreviewed":present,"missing":sum(r["status"]=="MISSING" for r in results),
       "warning_shots":sum(bool(r["warnings"]) for r in results),"human_review_needed":["single scene, not grid or player UI","photoreal backgrounds","normal human-to-furniture scale","consistent abstract character geometry","correct contact, occlusion and lighting"],
       "video_approved":False,"shots":results}
    Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"{present}/{len(results)} present; {report['missing']} missing; {report['warning_shots']} automated warning shots; visual review required")
    return 0 if present==len(results) and report["warning_shots"]==0 else 2

if __name__=="__main__": raise SystemExit(main())
