#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate a brand new high-tech ambient video via Seedance API and save it.

Usage:
  $env:SEEDANCE_API_KEY="your_api_key"
  $env:SEEDANCE_API_URL="https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks"
  $env:SEEDANCE_RESULT_API_URL_TEMPLATE="https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks/{task_id}"
  python scripts/generate_seedance_brand_video.py
"""

from __future__ import annotations

import os
import sys
import time
import json
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "exports" / "seedance_demo"
VIDEO_PATH = OUT_DIR / "mighty_skill_bridge_procedural_fallback.mp4"
MANIFEST_PATH = OUT_DIR / "manifest.json"

BRAND_PROMPT = (
    "Premium cinematic ambient loop of futuristic network connections. "
    "Glowing neon cyber blue and green laser light lines flowing, connecting nodes, "
    "representing AI agents, data synergy, technology bridge, dark mode, high-tech, "
    "8k resolution, smooth ambient motion, slow tracking pan"
)

def find_video_url(value):
    if isinstance(value, str):
        lowered = value.lower()
        if lowered.startswith(("http://", "https://")) and any(
            marker in lowered for marker in (".mp4", ".webm", ".mov", "video", "output")
        ):
            return value
        return None
    if isinstance(value, list):
        for item in value:
            found = find_video_url(item)
            if found:
                return found
        return None
    if isinstance(value, dict):
        preferred_keys = (
            "video_url", "url", "output_url", "download_url", 
            "content_url", "video", "videos", "output", "data", "result"
        )
        for key in preferred_keys:
            if key in value:
                found = find_video_url(value[key])
                if found:
                    return found
        for item in value.values():
            found = find_video_url(item)
            if found:
                return found
    return None

def find_task_id(value) -> str | None:
    if isinstance(value, dict):
        for key in ("task_id", "id", "request_id", "job_id"):
            if key in value and value[key]:
                return str(value[key])
        for item in value.values():
            found = find_task_id(item)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = find_task_id(item)
            if found:
                return found
    return None

def find_task_status(value) -> str | None:
    if isinstance(value, dict):
        for key in ("status", "task_status", "TaskStatus", "state", "State", "phase"):
            if key in value and value[key] is not None and not isinstance(value[key], (dict, list)):
                return str(value[key])
        for item in value.values():
            found = find_task_status(item)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = find_task_status(item)
            if found:
                return found
    return None

def main():
    api_key = os.environ.get("SEEDANCE_API_KEY") or os.environ.get("ARK_API_KEY")
    api_url = os.environ.get("SEEDANCE_API_URL")
    result_url_template = os.environ.get("SEEDANCE_RESULT_API_URL_TEMPLATE")
    model = os.environ.get("SEEDANCE_MODEL", "dreamina-seedance-2-0-260128")
    
    if not api_key or not api_url:
        print("[!] Seedance API credentials not fully set in environment variables.")
        print("Please configure them and run again:")
        print("  $env:SEEDANCE_API_KEY = \"<your_key>\"")
        print("  $env:SEEDANCE_API_URL = \"https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks\"")
        print("  $env:SEEDANCE_RESULT_API_URL_TEMPLATE = \"https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks/{task_id}\"")
        sys.exit(1)

    print(f"[*] Connecting to Seedance API at: {api_url}")
    print(f"[*] Prompt: \"{BRAND_PROMPT}\"")
    print(f"[*] Model: {model}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "content": [
            {
                "type": "text",
                "text": BRAND_PROMPT,
            }
        ],
        "ratio": "16:9",
        "duration": 6,
        "generate_audio": False,
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=45)
        if not response.ok:
            print(f"[-] Seedance generation request failed: {response.status_code} {response.reason}")
            print(response.text)
            sys.exit(1)
        
        create_payload = response.json()
        task_id = find_task_id(create_payload)
        
        if not task_id:
            print("[-] Error: Task ID not found in response payload.")
            print(json.dumps(create_payload, indent=2))
            sys.exit(1)
            
        print(f"[+] Task successfully created! Task ID: {task_id}")
        
        if not result_url_template:
            print("[!] Warning: SEEDANCE_RESULT_API_URL_TEMPLATE is not set. Cannot poll for result.")
            print("Please retrieve the video manually or set the result template variable.")
            sys.exit(0)
            
        poll_url = result_url_template.format(task_id=task_id)
        print(f"[*] Starting result polling at: {poll_url}")
        
        timeout = 300
        interval = 10
        deadline = time.monotonic() + timeout
        video_url = None
        
        while time.monotonic() < deadline:
            poll_resp = requests.get(poll_url, headers=headers, timeout=45)
            if not poll_resp.ok:
                print(f"[-] Polling failed: {poll_resp.status_code} {poll_resp.reason}")
                time.sleep(interval)
                continue
                
            poll_payload = poll_resp.json()
            status = find_task_status(poll_payload) or "running"
            print(f"[*] Task status: {status}")
            
            video_url = find_video_url(poll_payload)
            if video_url:
                print(f"[+] Video generation completed successfully!")
                break
                
            if status.lower() in ("failed", "cancelled", "error"):
                print(f"[-] Task failed on provider side with status: {status}")
                print(json.dumps(poll_payload, indent=2))
                sys.exit(1)
                
            time.sleep(interval)
            
        if not video_url:
            print(f"[-] Timeout: Video generation was not completed within {timeout} seconds.")
            sys.exit(1)
            
        print(f"[*] Downloading generated video from: {video_url}")
        video_resp = requests.get(video_url, timeout=90, stream=True)
        if not video_resp.ok:
            print(f"[-] Failed to download video: {video_resp.status_code} {video_resp.reason}")
            sys.exit(1)
            
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(VIDEO_PATH, "wb") as f:
            for chunk in video_resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        print(f"[+] Brand video successfully downloaded and statically placed at:")
        print(f"  - {VIDEO_PATH}")
        
        # Update local manifest.json
        manifest = {}
        if MANIFEST_PATH.exists():
            try:
                manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            except Exception:
                manifest = {}
                
        manifest.update({
            "hero_brand_video": {
                "status": "ready",
                "provider": "seedance_api_brand_loop",
                "model": model,
                "task_id": task_id,
                "video": VIDEO_PATH.relative_to(PROJECT_ROOT).as_posix(),
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "prompt": BRAND_PROMPT
            }
        })
        MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=4), encoding="utf-8")
        print(f"[+] Updated manifest: {MANIFEST_PATH}")
        
    except Exception as e:
        print(f"[-] Exception occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
