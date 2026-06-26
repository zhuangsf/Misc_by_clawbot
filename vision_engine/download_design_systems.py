#!/usr/bin/env python3
"""下载 awesome-design-md 的所有设计系统"""

import os
import requests
import json
import concurrent.futures

BASE_URL = "https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md"
OUTPUT_DIR = "/root/.openclaw/workspace/vision_engine/design_systems"

# 品牌列表
BRANDS = [
    "airbnb", "airtable", "apple", "bmw", "cal", "claude", "clay", "clickhouse",
    "cohere", "coinbase", "composio", "cursor", "elevenlabs", "expo", "figma",
    "framer", "hashicorp", "ibm", "intercom", "kraken", "linear.app", "lovable",
    "minimax", "mintlify", "miro", "mistral.ai", "mongodb", "notion", "nvidia",
    "ollama", "opencode.ai", "pinterest", "posthog", "raycast", "replicate",
    "resend", "revolut", "runwayml", "sanity", "sentry", "spacex", "spotify",
    "stripe", "supabase", "superhuman", "together.ai", "uber", "vercel",
    "voltagent", "warp", "webflow", "wise", "x.ai", "zapier"
]

def download_brand(brand):
    """下载单个品牌的文件"""
    brand_dir = os.path.join(OUTPUT_DIR, brand)
    os.makedirs(brand_dir, exist_ok=True)
    
    results = {"brand": brand, "design_md": False, "preview_html": False}
    
    try:
        # 下载 DESIGN.md
        design_url = f"{BASE_URL}/{brand}/DESIGN.md"
        response = requests.get(design_url, timeout=15)
        if response.status_code == 200:
            with open(os.path.join(brand_dir, "DESIGN.md"), 'w', encoding='utf-8') as f:
                f.write(response.text)
            results["design_md"] = True
        
        # 下载 preview.html
        preview_url = f"{BASE_URL}/{brand}/preview.html"
        response = requests.get(preview_url, timeout=15)
        if response.status_code == 200:
            with open(os.path.join(brand_dir, "preview.html"), 'w', encoding='utf-8') as f:
                f.write(response.text)
            results["preview_html"] = True
    except Exception as e:
        print(f"  Error downloading {brand}: {e}")
    
    return results

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    success_count = 0
    failed_brands = []
    
    print(f"Starting parallel download of {len(BRANDS)} brands...")
    print(f"Using {min(10, len(BRANDS))} concurrent workers\n")
    
    # 使用线程池并行下载
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_brand = {executor.submit(download_brand, brand): brand for brand in BRANDS}
        
        for future in concurrent.futures.as_completed(future_to_brand):
            result = future.result()
            brand = result["brand"]
            
            if result["design_md"]:
                success_count += 1
                print(f"✓ {brand}")
            else:
                failed_brands.append(brand)
                print(f"✗ {brand} (failed)")
    
    print(f"\n{'='*50}")
    print(f"Downloaded: {success_count}/{len(BRANDS)} brands")
    if failed_brands:
        print(f"Failed: {', '.join(failed_brands)}")
    print(f"Output: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
