import os
import re
import glob
import json
import requests
from bs4 import BeautifulSoup
import time

def load_products_from_md():
    current_dir = os.getcwd()
    files = glob.glob(os.path.join(current_dir, "_XQ*Pharma*.md"))
    if not files: return []
    
    with open(files[0], "r", encoding="utf-8") as f:
        content = f.read()
    
    sections = content.split("---")
    products = []
    for sect in sections:
        if not sect.strip(): continue
        lines = [l.strip() for l in sect.split("\n") if l.strip()]
        if not lines: continue
        name = lines[0].replace("#", "").strip()
        link_match = re.search(r"\[Link\]\((.*?)\)", sect)
        link = link_match.group(1).strip() if link_match else ""
        if name and link:
            products.append({"name": name, "link": link})
    return products

def sync_images():
    products = load_products_from_md()
    mapping = {}
    print(f"Syncing images for {len(products)} products...")
    
    for p in products:
        name = p["name"]
        url = p["link"]
        if not url: continue
        
        try:
            print(f"Fetching {name}...", end=" ", flush=True)
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Try OG Image first
                og_image = soup.find("meta", property="og:image")
                if og_image:
                    img_url = og_image["content"]
                else:
                    # Fallback to first product image
                    img_url = ""
                
                if img_url:
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url
                    mapping[name] = img_url
                    print("✅")
                else:
                    print("❓ No image found")
            else:
                print(f"❌ HTTP {resp.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(0.5) # Be gentle

    with open("product_images.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=4)
    print("\nDone! Saved to product_images.json")

if __name__ == "__main__":
    sync_images()
