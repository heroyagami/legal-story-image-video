#!/usr/bin/env python3
"""Combine fixed transparent role art and a real AI scene image. Does NOT generate the images."""
from __future__ import annotations
import argparse, hashlib, io, json
from pathlib import Path
from PIL import Image

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_role(path):
    if path.suffix.lower() == ".svg":
        try:
            import cairosvg
        except ImportError as error:
            raise RuntimeError("Install cairosvg for SVG roles or supply transparent PNGs") from error
        role = Image.open(io.BytesIO(cairosvg.svg2png(url=str(path)))).convert("RGBA")
    else:
        with Image.open(path) as src:
            if src.mode not in ("RGBA", "LA") and "transparency" not in src.info:
                raise ValueError(f"Not a true alpha character: {path}")
            role = src.convert("RGBA")
    amin, amax = role.getchannel("A").getextrema()
    if amin == 255 or amax == 0:
        raise ValueError(f"Character has invalid alpha: {path}")
    return role

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--scene", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args=parser.parse_args()
    root=args.asset_root.resolve()
    item=json.loads(args.scene.read_text(encoding="utf-8"))
    def source(relative):
        path=(root/relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"Missing or outside asset root: {relative}")
        return path
    back=source(item["background"])
    with Image.open(back) as img:
        base=img.convert("RGBA")
    output=base.copy()
    report={"background_sha256":sha(back), "roles":[], "visual_review":"PENDING", "video_approved":False}
    for actor in item.get("roles",[]):
        path=source(actor["asset"])
        x,y,w,h=actor["box"]
        if any(not isinstance(v,int) for v in (x,y,w,h)) or w<=0 or h<=0 or x<0 or y<0 or x+w>output.width or y+h>output.height:
            raise ValueError(f"Invalid character placement: {actor['role_id']}")
        rgba=load_role(path).resize((w,h),Image.Resampling.LANCZOS)
        output.alpha_composite(rgba,(x,y))
        report["roles"].append({"role_id":actor["role_id"],"asset_sha256":sha(path),"box":actor["box"],
                                "scale_anchors":actor.get("scale_anchors",[]),"pose":actor.get("pose","unspecified")})
    mask_relative=item.get("foreground_occlusion_mask")
    if mask_relative:
        mask_path=source(mask_relative)
        with Image.open(mask_path) as src:
            mask=src.convert("L")
        if mask.size != output.size:
            raise ValueError("Occlusion mask dimensions mismatch")
        output=Image.composite(base,output,mask)
        report["occlusion_sha256"]=sha(mask_path)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    output.convert("RGB").save(args.out)
    report["out"]=str(args.out)
    args.out.with_suffix(args.out.suffix+".qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Wrote {args.out}; HUMAN VISUAL REVIEW REQUIRED")
if __name__=="__main__":
    main()
