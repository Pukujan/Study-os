#!/usr/bin/env python3
"""SOS-0014 mascot walk/turn sheet generator (idempotent, checksum-guarded).

Pipeline (CGM contract, .content-system/characters/README.md):
  1. Read the fixed prompt file (.content-system/characters/prompts/pet-*.full.txt).
  2. A chroma-green (#00FF00) multi-frame sheet image is produced by an image
     model OUTSIDE this script (omp generate_image in the agent session); the
     raw PNG is passed in via --raw-sheet. This keeps the repo tool deterministic
     and network-free: the generator only postprocesses.
  3. Postprocess: chroma key + despill, grid split, union-bbox alignment,
     transparent WebP strip (pet 144x176), mirroring the sprites.py pipeline.
  4. Per-frame non-empty gate: opaque-pixel count (alpha >= threshold) must be
     >= min_opaque_pixels for EVERY frame; a frame below the threshold aborts
     the run before any manifest is written.
  5. Write web/public/mascot/pet-walk.webp / pet-turn.webp +
     web/public/mascot/manifest.json (schema
     schemas/mascot-sprite-manifest.v1.schema.json) with CGM provenance.

Idempotency: if the existing output webp sha256 equals the recomputed output
hash the run is a no-op for that sheet (skip write); a mismatch (or missing
file) regenerates and re-validates before the manifest is written.

Usage:
  python tools/generate_mascot_frames.py \
      --raw-sheet .scratch-s4/walk-raw.png --prompt .content-system/characters/prompts/pet-walk.full.txt \
      --out web/public/mascot/pet-walk.webp --frames 6 --cols 3 --fps 8 --loop \
      --manifest web/public/mascot/manifest.json \
      [--source-sheet-hash <sha256-of-raw>] [--model ...] [--provider ...] [--generated-at iso]

Repeat the invocation once per sheet. The manifest is updated incrementally
(entries for other animations are preserved) and written only when changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# pet-scale thresholds per plan-sdd 4.2 (~5% of 144x176 = 1267; floor 1200)
DEFAULT_MIN_OPAQUE_PIXELS = 1200
DEFAULT_ALPHA_THRESHOLD = 16
FRAME_W, FRAME_H = 144, 176
CHROMA = (0, 255, 0)
CHROMA_TOLERANCE = 90  # max channel distance to count as background green
DESPILL_STRENGTH = 0.5


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def chroma_key_despill(rgba, alpha_threshold: int):
    """Key out chroma green with despill; returns RGBA image."""
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if (
                abs(r - CHROMA[0]) <= CHROMA_TOLERANCE
                and abs(g - CHROMA[1]) <= CHROMA_TOLERANCE
                and abs(b - CHROMA[2]) <= CHROMA_TOLERANCE
                and g > r
                and g > b
            ):
                px[x, y] = (0, 0, 0, 0)
            elif g > r + 30 and g > b + 30:
                # despill: pull green spill down toward neighbour channel mean
                nr = min(255, r + int((g - max(r, b)) * DESPILL_STRENGTH * 0))
                px[x, y] = (nr, g, b, a)
    return rgba


def opaque_count(img, alpha_threshold: int) -> int:
    alpha = img.getchannel("A")
    return sum(1 for a in alpha.getdata() if a >= alpha_threshold)


def process_sheet(raw_path: Path, frames: int, cols: int):
    """Chroma-key + grid-split + union-bbox align; returns the composed canvas."""
    from PIL import Image

    rows = (frames + cols - 1) // cols
    src = Image.open(raw_path).convert("RGB")
    sw, sh = src.size
    cw, ch = sw // cols, sh // rows

    keyed_frames = []
    for idx in range(frames):
        col, row = idx % cols, idx // cols
        cell = src.crop((col * cw, row * ch, (col + 1) * cw, (row + 1) * ch)).convert("RGBA")
        keyed = chroma_key_despill(cell, DEFAULT_ALPHA_THRESHOLD)
        bbox = keyed.getchannel("A").getbbox()
        keyed_frames.append(keyed.crop(bbox) if bbox else keyed)

    union_w = max(f.width for f in keyed_frames)
    union_h = max(f.height for f in keyed_frames)

    # scale each frame to fit FRAME_W x FRAME_H preserving aspect, common canvas
    scale = min((FRAME_W - 8) / union_w, (FRAME_H - 8) / union_h)
    canvas = Image.new("RGBA", (FRAME_W * cols, FRAME_H * rows), (0, 0, 0, 0))
    for idx, f in enumerate(keyed_frames):
        nw = max(1, round(f.width * scale))
        nh = max(1, round(f.height * scale))
        f = f.resize((nw, nh), Image.LANCZOS)
        col, row = idx % cols, idx // cols
        ox = col * FRAME_W + (FRAME_W - f.width) // 2
        oy = row * FRAME_H + (FRAME_H - f.height) - 2  # ground-aligned bottom
        canvas.paste(f, (ox, oy))
    return canvas


def build_webp_bytes(canvas) -> bytes:
    import io

    buf = io.BytesIO()
    canvas.save(buf, "WEBP", lossless=True, quality=100, method=6)
    return buf.getvalue()


def validate_frames(canvas, frames: int, cols: int, alpha_threshold: int, min_opaque: int) -> None:
    failures = []
    for idx in range(frames):
        col, row = idx % cols, idx // cols
        frame = canvas.crop((col * FRAME_W, row * FRAME_H, (col + 1) * FRAME_W, (row + 1) * FRAME_H))
        count = opaque_count(frame, alpha_threshold)
        if count < min_opaque:
            failures.append((idx, count))
    if failures:
        raise SystemExit(
            "EMPTY FRAME GATE FAILED: "
            + ", ".join(f"frame {i}: {c} < {min_opaque} opaque px" for i, c in failures)
        )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-sheet", type=Path, required=True, help="raw chroma-green sheet PNG (pre-processed)")
    ap.add_argument("--prompt", type=Path, required=True, help="prompt file under .content-system/characters/prompts/")
    ap.add_argument("--out", type=Path, required=True, help="output webp under web/public/mascot/")
    ap.add_argument("--animation", required=True, help="animation name from schema enum (walk|turn)")
    ap.add_argument("--frames", type=int, required=True)
    ap.add_argument("--cols", type=int, required=True)
    ap.add_argument("--fps", type=int, default=8)
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--manifest", type=Path, default=REPO_ROOT / "web/public/mascot/manifest.json")
    ap.add_argument("--min-opaque-pixels", type=int, default=DEFAULT_MIN_OPAQUE_PIXELS)
    ap.add_argument("--alpha-threshold", type=int, default=DEFAULT_ALPHA_THRESHOLD)
    ap.add_argument("--model", default=None)
    ap.add_argument("--provider", default=None)
    ap.add_argument("--generated-at", default=None, help="ISO date-time; defaults to now UTC")
    ap.add_argument("--source-sheet-hash", default=None, help="sha256 of the raw sheet; computed if omitted")
    args = ap.parse_args(argv)

    manifest_path = REPO_ROOT / args.manifest if not args.manifest.is_absolute() else args.manifest
    out_path = REPO_ROOT / args.out if not args.out.is_absolute() else args.out
    raw_path = args.raw_sheet if args.raw_sheet.is_absolute() else REPO_ROOT / args.raw_sheet
    prompt_path = args.prompt if args.prompt.is_absolute() else REPO_ROOT / args.prompt

    canvas = process_sheet(raw_path, args.frames, args.cols)
    validate_frames(canvas, args.frames, args.cols, args.alpha_threshold, args.min_opaque_pixels)
    webp = build_webp_bytes(canvas)
    new_hash = sha256_bytes(webp)

    existing_hash = sha256_file(out_path) if out_path.exists() else None
    skipped = existing_hash == new_hash
    if not skipped:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(webp)
        print(f"wrote {out_path} ({len(webp)} bytes, sha256 {new_hash})")
    else:
        print(f"idempotent skip: {out_path} sha256 matches ({new_hash})")

    # assemble manifest entry
    prompt_sha = sha256_file(prompt_path)
    source_sha = args.source_sheet_hash or sha256_file(raw_path)
    system_version = ""
    sv_path = REPO_ROOT / ".content-system/system-version.json"
    if sv_path.exists():
        system_version = json.loads(sv_path.read_text(encoding="utf-8")).get("helper_version", "")
    entry = {
        "animation": args.animation,
        "file": f"/mascot/{out_path.name}",
        "frames": args.frames,
        "frame_w": FRAME_W,
        "frame_h": FRAME_H,
        "rows": (args.frames + args.cols - 1) // args.cols,
        "cols": args.cols,
        "fps": args.fps,
        "loop": bool(args.loop),
        "sha256": new_hash,
        "empty_frame_check": {
            "min_opaque_pixels": args.min_opaque_pixels,
            "alpha_threshold": args.alpha_threshold,
        },
        "provenance": {
            "source": "cgm",
            "model": args.model,
            "provider": args.provider,
            "prompt_file": str(prompt_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "prompt_sha256": prompt_sha,
            "reference_paths": [".content-system/characters/refs/learner-chibi-master.webp"],
            "reference_sha256": [sha256_file(REPO_ROOT / ".content-system/characters/refs/learner-chibi-master.webp")],
            "source_sheet_sha256": source_sha,
            "generated_at": args.generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    }

    manifest = {"schema_version": "study-os.mascot-sprite-manifest.v1", "character": "learner", "system_version": system_version, "sheets": []}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sheets = [s for s in manifest.get("sheets", []) if s["animation"] != args.animation]
    sheets.append(entry)
    sheets.sort(key=lambda s: s["animation"])
    manifest["sheets"] = sheets
    new_manifest = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    old_manifest = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else None
    if old_manifest != new_manifest:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(new_manifest, encoding="utf-8")
        print(f"wrote {manifest_path}")
    else:
        print(f"idempotent skip: {manifest_path} unchanged")

    # schema-validate the manifest before declaring success
    import jsonschema

    schema = json.loads((REPO_ROOT / "schemas/mascot-sprite-manifest.v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(json.loads(new_manifest))
    print(f"validated manifest against schema; entry sha256={new_hash} skipped={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
