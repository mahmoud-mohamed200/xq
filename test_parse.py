import os
import re
import glob

def _load_products():
    current_dir = os.getcwd()
    files = glob.glob(os.path.join(current_dir, "_XQ*Pharma*.md"))
    if not files:
        print("No files found")
        return []
    
    with open(files[0], "r", encoding="utf-8") as f:
        content = f.read()
    
    sections = content.split("---")
    products = []
    for sect in sections:
        if not sect.strip(): continue
        lines = [l.strip() for l in sect.split("\n") if l.strip()]
        if not lines: continue
        name = lines[0].replace("#", "").strip()
        id_match = re.search(r"\*\*ID:\*\*\s*(.*)", sect)
        pid = id_match.group(1).strip() if id_match else ""
        desc_match = re.search(r"\*\*Description:\*\*\s*(.*)", sect)
        desc = desc_match.group(1).strip() if desc_match else ""
        link_match = re.search(r"\[Link\]\((.*?)\)", sect)
        link = link_match.group(1).strip() if link_match else ""
        if name and (desc or link):
            products.append({"name": name, "id": pid, "description": desc, "link": link})
    return products

prods = _load_products()
print(f"Loaded {len(prods)} products")
for p in prods[:3]:
    print(p)
