#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate a small local demo video for the Seedance-style public demo.

The file is intentionally generated from project-owned procedural frames. It is
used as the public/static fallback when Seedance API credentials are not set.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "exports" / "seedance_demo"
FRAMES_DIR = OUT_DIR / "_frames"
VIDEO_PATH = OUT_DIR / "mighty_skill_bridge_seedance_demo.mp4"
MANIFEST_PATH = OUT_DIR / "manifest.json"

WIDTH = 1280
HEIGHT = 720
FPS = 12
SECONDS = 6
FRAME_COUNT = FPS * SECONDS


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/YuGothB.ttc" if bold else "C:/Windows/Fonts/YuGothR.ttc"),
        Path("C:/Windows/Fonts/meiryob.ttc" if bold else "C:/Windows/Fonts/meiryo.ttc"),
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size=size)
            except OSError:
                pass
    return ImageFont.load_default()


FONT_HERO = load_font(70, bold=True)
FONT_TITLE = load_font(34, bold=True)
FONT_BODY = load_font(24)
FONT_SMALL = load_font(18, bold=True)


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def make_gradient(t: float) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), "#040405")
    px = img.load()
    pulse = 0.5 + 0.5 * math.sin(t * math.tau)
    for y in range(HEIGHT):
        yy = y / HEIGHT
        for x in range(WIDTH):
            xx = x / WIDTH
            glow_a = max(0.0, 1.0 - math.hypot(xx - (0.22 + 0.1 * pulse), yy - 0.32) / 0.72)
            glow_b = max(0.0, 1.0 - math.hypot(xx - (0.78 - 0.08 * pulse), yy - 0.52) / 0.62)
            r = lerp(4, 20, yy) + int(glow_b * 42)
            g = lerp(5, 18, yy) + int(glow_a * 48) + int(glow_b * 34)
            b = lerp(6, 22, yy) + int(glow_a * 78)
            px[x, y] = (min(r, 255), min(g, 255), min(b, 255))
    return img.filter(ImageFilter.GaussianBlur(radius=0.4))


def rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], radius: int, fill: str, outline: str | None = None, width: int = 1) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_grid(draw: ImageDraw.ImageDraw, offset: int) -> None:
    for x in range(-120 + offset, WIDTH + 120, 80):
        draw.line((x, 0, x, HEIGHT), fill=(255, 255, 255, 16), width=1)
    for y in range(-80 + offset // 2, HEIGHT + 80, 80):
        draw.line((0, y, WIDTH, y), fill=(255, 255, 255, 14), width=1)


def draw_frame(index: int) -> Image.Image:
    t = index / FRAME_COUNT
    img = make_gradient(t)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_grid(draw, int((t * 80) % 80))

    # Cinematic crop bars.
    draw.rectangle((0, 0, WIDTH, 54), fill=(0, 0, 0, 120))
    draw.rectangle((0, HEIGHT - 54, WIDTH, HEIGHT), fill=(0, 0, 0, 120))

    # Main luminous panel.
    panel_x = 76 + int(math.sin(t * math.tau) * 10)
    panel_y = 94
    rounded_rect(draw, (panel_x, panel_y, panel_x + 628, panel_y + 420), 20, (0, 0, 0, 114), (255, 255, 255, 42), 2)
    draw.text((panel_x + 40, panel_y + 42), "Mighty Skill-Bridge", font=FONT_TITLE, fill=(255, 255, 250, 255))
    draw.text((panel_x + 40, panel_y + 94), "Engineer x Project", font=FONT_HERO, fill=(255, 255, 250, 255))
    draw.text((panel_x + 42, panel_y + 184), "prompt-to-video fit preview", font=FONT_BODY, fill=(190, 200, 206, 255))

    labels = [("Skill", 0.92), ("Culture", 0.88), ("Growth", 0.95), ("Performing", 0.84)]
    for i, (label, value) in enumerate(labels):
        y = panel_y + 242 + i * 40
        draw.text((panel_x + 42, y - 4), label, font=FONT_SMALL, fill=(235, 238, 240, 255))
        draw.rounded_rectangle((panel_x + 196, y + 2, panel_x + 520, y + 14), radius=6, fill=(255, 255, 255, 36))
        color = [(139, 220, 255), (186, 255, 102), (255, 209, 102), (255, 108, 171)][i]
        animated = min(1.0, value * (0.78 + 0.22 * math.sin((t + i * 0.11) * math.tau) ** 2))
        draw.rounded_rectangle((panel_x + 196, y + 2, panel_x + 196 + int(324 * animated), y + 14), radius=6, fill=(*color, 255))

    # Right video tile stack.
    for i in range(3):
        x0 = 780 + i * 42
        y0 = 116 + i * 72
        rounded_rect(draw, (x0, y0, x0 + 360, y0 + 190), 18, (255, 255, 255, 18), (255, 255, 255, 46), 1)
        stripe = int((t * 360 + i * 70) % 360)
        draw.rectangle((x0 + stripe, y0, x0 + stripe + 26, y0 + 190), fill=(139, 220, 255, 52))
        draw.text((x0 + 26, y0 + 28), ["resume", "project", "match"][i], font=FONT_TITLE, fill=(255, 255, 255, 230))

    # Playhead.
    playhead_x = 112 + int(t * (WIDTH - 224))
    draw.rounded_rectangle((112, HEIGHT - 88, WIDTH - 112, HEIGHT - 78), radius=5, fill=(255, 255, 255, 40))
    draw.rounded_rectangle((112, HEIGHT - 88, playhead_x, HEIGHT - 78), radius=5, fill=(186, 255, 102, 255))
    draw.ellipse((playhead_x - 10, HEIGHT - 98, playhead_x + 10, HEIGHT - 68), fill=(255, 255, 255, 255))

    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(parents=True)

    for index in range(FRAME_COUNT):
        draw_frame(index).save(FRAMES_DIR / f"frame_{index:04d}.png")

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required to generate the demo video.")

    command = [
        ffmpeg,
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(FRAMES_DIR / "frame_%04d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-t",
        str(SECONDS),
        str(VIDEO_PATH),
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    shutil.rmtree(FRAMES_DIR)

    manifest = {
        "status": "ready",
        "provider": "local_seedance_demo_asset",
        "video": VIDEO_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "fps": FPS,
        "duration_seconds": SECONDS,
        "resolution": f"{WIDTH}x{HEIGHT}",
        "note": "Procedural Mighty-owned fallback video for Seedance API demo UI.",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] Seedance demo video generated: {VIDEO_PATH}")
    print(f"[*] Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
