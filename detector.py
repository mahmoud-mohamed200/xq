"""
Skin Problem Detection Agent
Uses Roboflow's multi-class model via REST API to detect skin conditions.
"""

import os
import json
import base64
import time
import requests
import uuid
from google import genai
from datetime import datetime
from config import (
    ROBOFLOW_API_KEY, ROBOFLOW_API_URL, MODEL_ID,
    CONFIDENCE_THRESHOLD, OVERLAP_THRESHOLD, SKIN_CONDITIONS,
    GEMINI_API_KEY
)


class SkinDetectionAgent:
    """AI Agent for detecting skin problems using Roboflow's multi-class model."""

    def __init__(self):
        """Initialize the detection agent."""
        self.api_url = f"{ROBOFLOW_API_URL}/{MODEL_ID}"
        self.detection_history = []
        self.results_cache = {}  # Store full results for feedback matching
        if GEMINI_API_KEY:
            self._llm = genai.Client(api_key=GEMINI_API_KEY)
        else:
            self._llm = None
        print(f"[SkinAgent] Initialized with model: {MODEL_ID}")
        print(f"[SkinAgent] API endpoint: {self.api_url}")

    def _call_roboflow_api(self, image_path=None, image_b64=None, image_url=None):
        """
        Call the Roboflow hosted inference API.

        Args:
            image_path: Local file path to upload
            image_b64: Base64-encoded image string
            image_url: URL of the image

        Returns:
            Raw API response as dict
        """
        params = {
            "api_key": ROBOFLOW_API_KEY,
            "confidence": CONFIDENCE_THRESHOLD,
            "overlap": OVERLAP_THRESHOLD,
        }

        try:
            if image_url:
                # Use URL-based inference
                params["image"] = image_url
                response = requests.post(self.api_url, params=params)
            elif image_path:
                # Upload file as base64
                with open(image_path, "rb") as f:
                    img_bytes = f.read()
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                response = requests.post(
                    self.api_url,
                    params=params,
                    data=img_b64,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
            elif image_b64:
                # Direct base64
                response = requests.post(
                    self.api_url,
                    params=params,
                    data=image_b64,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
            else:
                raise ValueError("No image source provided")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            msg = e.response.text
            status = e.response.status_code
            if status == 403:
                msg = ("Roboflow API Error 403 Forbidden. Your API key works, but this specific "
                       "community model has not been cloned to your workspace. "
                       "Please go to roboflow.com, find 'Skin-Problem-Detection-Relabel-Clean3', "
                       "and clone it to your 'bebooo' workspace, then update MODEL_ID in config.py.")
            elif status == 404:
                msg = ("Roboflow API 404 Not Found. You successfully cloned the dataset to your workspace, "
                       "but the model hasn't been trained yet! Please go to your project in Roboflow, "
                       "click on 'Versions', select Version 1, and click 'Train' (Fast/Accurate). "
                       "Once training completes, the API will become active automatically.")
            raise ValueError(f"API Error ({status}): {msg}")

    def detect_from_file(self, image_path: str, age: str = None, skin_type: str = None) -> dict:
        """
        Run skin detection on a local image file.
        """
        if not os.path.exists(image_path):
            return {"error": f"Image file not found: {image_path}", "success": False}

        try:
            start_time = time.time()
            result = self._call_roboflow_api(image_path=image_path)
            inference_time = round((time.time() - start_time) * 1000, 2)

            analysis = self._analyze_results(result, inference_time, age, skin_type)

            self.detection_history.append({
                "timestamp": datetime.now().isoformat(),
                "source": image_path,
                "summary": analysis["summary"]
            })

            return analysis
        except Exception as e:
            return {"error": str(e), "success": False}

    def detect_from_base64(self, image_b64: str, age: str = None, skin_type: str = None) -> dict:
        """
        Run skin detection on a base64 encoded image.
        """
        try:
            start_time = time.time()
            result = self._call_roboflow_api(image_b64=image_b64)
            inference_time = round((time.time() - start_time) * 1000, 2)

            analysis = self._analyze_results(result, inference_time, age, skin_type)

            self.detection_history.append({
                "timestamp": datetime.now().isoformat(),
                "source": "base64_upload",
                "summary": analysis["summary"]
            })

            return analysis
        except Exception as e:
            return {"error": str(e), "success": False}

    def detect_from_url(self, image_url: str, age: str = None, skin_type: str = None) -> dict:
        """
        Run skin detection on an image URL.
        """
        try:
            start_time = time.time()
            result = self._call_roboflow_api(image_url=image_url)
            inference_time = round((time.time() - start_time) * 1000, 2)

            analysis = self._analyze_results(result, inference_time, age, skin_type)

            self.detection_history.append({
                "timestamp": datetime.now().isoformat(),
                "source": image_url,
                "summary": analysis["summary"]
            })

            return analysis
        except Exception as e:
            return {"error": str(e), "success": False}

    def _load_products(self) -> list:
        """Load and parse product catalog from markdown file."""
        import glob
        import re
        # Use glob to handle the special character in the filename
        current_dir = os.path.dirname(os.path.abspath(__file__))
        files = glob.glob(os.path.join(current_dir, "_XQ*Pharma*.md"))
        
        if not files:
            print("[SkinAgent] Product catalog not found.")
            return []
        
        try:
            with open(files[0], "r", encoding="utf-8") as f:
                content = f.read()
            
            # Simple splitter for products (---)
            sections = content.split("---")
            products = []
            for sect in sections:
                if not sect.strip(): continue
                
                # Extract Title (first non-empty line)
                lines = [l.strip() for l in sect.split("\n") if l.strip()]
                if not lines: continue
                name = lines[0].replace("#", "").strip()
                
                # Extract ID
                id_match = re.search(r"\*\*ID:\*\*\s*(.*)", sect)
                pid = id_match.group(1).strip() if id_match else ""
                
                # Extract Description
                desc_match = re.search(r"\*\*Description:\*\*\s*(.*)", sect)
                desc = desc_match.group(1).strip() if desc_match else ""
                
                # Extract Link
                link_match = re.search(r"\[Link\]\((.*?)\)", sect)
                link = link_match.group(1).strip() if link_match else ""
                
                if name and (desc or link):
                    products.append({
                        "name": name,
                        "id": pid,
                        "description": desc,
                        "link": link
                    })
            
            print(f"[SkinAgent] Loaded {len(products)} products from catalog.")
            return products
        except Exception as e:
            print(f"[SkinAgent] Error loading products: {e}")
            return []

    def _generate_diet_and_products(self, unique_conditions: list, age: str = None, skin_type: str = None) -> tuple:
        """Call Gemini to generate a diet plan and product recommendations."""
        if not self._llm:
            return "مفتاح API الخاص بـ Gemini مفقود في config.py.", []
        
        if not unique_conditions:
            return "لم يتم اكتشاف أي مشاكل جلدية. حافظ على نظامك الغذائي الصحي الحالي.", []

        products_catalog = self._load_products()
        catalog_str = ""
        for p in products_catalog:
            catalog_str += f"- {p['name']}: {p['description']} (ID: {p['id']})\n"

        condition_names = ", ".join(unique_conditions)
        profile_parts = []
        if age: profile_parts.append(f"يبلغ من العمر {age} عاماً")
        if skin_type: profile_parts.append(f"نوع بشرته: {skin_type}")
        profile_context = f"معلومات المستخدم: {' و '.join(profile_parts)}." if profile_parts else ""

        prompt = f"""
        يعاني المستخدم من الحالات الجلدية التالية: {condition_names}.
        {profile_context}
        
        بصفتك خبير تغذية وأمراض جلدية، قم بمهمتين:
        1. إعداد خطة غذائية موجزة (2-4 نقاط). اذكر الأطعمة التي ينصح بها والتي يجب تجنبها.
        2. اختر بحد أقصى 3 منتجات مناسبة تمامًا لهذه الحالات من كتالوج منتجات XQ Pharma المرفق أدناه.
        
        الكتالوج:
        {catalog_str}
        
        يجب أن يكون الرد بتنسيق JSON حصرياً كما يلي:
        {{
            "diet_plan": "نص الخطة الغذائية بالعربية هنا...",
            "recommendations": [
                {{
                    "product_name": "اسم المنتج كما هو في الكتالوج",
                    "reason_ar": "لماذا هذا المنتج مناسب لهذه الحالة بالعربية",
                    "id": "معرف المنتج ID"
                }}
            ]
        }}
        
        اكتب باللغة العربية. تأكد من أن الرد JSON صالح.
        """
        
        # Try multiple models that were confirmed to work in diagnostic tests
        models_to_try = ['gemini-flash-latest', 'gemini-2.5-flash']
        
        def normalize(s):
            """Normalize string for better matching (lowercase, strip special spaces)."""
            import re
            if not s: return ""
            # Replace narrow no-break space (u202f) and other whitespace
            s = s.replace("\u202f", " ").replace("\u00a0", " ")
            s = re.sub(r"\s+", " ", s).strip().lower()
            return s

        last_error = ""
        for model_name in models_to_try:
            try:
                print(f"[SkinAgent] Attempting LLM with {model_name}...")
                response = self._llm.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        'response_mime_type': 'application/json'
                    }
                )
                data = json.loads(response.text.strip())
                
                diet_plan = data.get("diet_plan", "")
                recs = data.get("recommendations", [])
                
                # Enrich recommendations with links from catalog
                final_recs = []
                for r in recs:
                    req_id = normalize(r.get("id", ""))
                    req_name = normalize(r.get("product_name", ""))
                    
                    catalog_item = None
                    for p in products_catalog:
                        p_id = normalize(p.get("id", ""))
                        p_name = normalize(p.get("name", ""))
                        if (req_id and req_id in p_id) or (req_name and req_name in p_name) or (p_name and p_name in req_name):
                            catalog_item = p
                            break
                    
                    if catalog_item:
                        name_lower = catalog_item["name"].lower()
                        icon = "🧴" # Default
                        if "cleanser" in name_lower or "غسول" in catalog_item["name"]: icon = "🧼"
                        elif "serum" in name_lower or "سيروم" in catalog_item["name"]: icon = "🧪"
                        elif "shampoo" in name_lower or "شامبو" in catalog_item["name"]: icon = "🚿"
                        elif "mask" in name_lower or "ماسك" in catalog_item["name"]: icon = "🎭"
                        elif "gel" in name_lower or "جل" in catalog_item["name"]: icon = "💧"
                        
                        # Load real product images if available
                        image_url = ""
                        try:
                            # Use absolute path relative to this file
                            base_dir = os.path.dirname(os.path.abspath(__file__))
                            images_path = os.path.join(base_dir, "product_images.json")
                            with open(images_path, "r", encoding="utf-8") as f:
                                img_map = json.load(f)
                                image_url = img_map.get(catalog_item["name"], "")
                        except Exception as e:
                            print(f"[SkinAgent] Error loading image for {catalog_item['name']}: {e}")
                            pass

                        final_recs.append({
                            "name": catalog_item["name"],
                            "reason": r.get("reason_ar", ""),
                            "link": catalog_item["link"],
                            "icon": icon,
                            "image_url": image_url,
                            "brand_logo": "xq-logo.avif"
                        })
                
                print(f"[SkinAgent] ✅ Success with {model_name}. Matched {len(final_recs)} products.")
                return diet_plan, final_recs
                
            except Exception as e:
                last_error = str(e)
                print(f"[SkinAgent] ❌ Error with {model_name}: {last_error}")
                if "404" in last_error or "429" in last_error or "503" in last_error:
                    time.sleep(1) # Brief wait before trying fallback
                    continue
                break # Non-recoverable error
        
        # If we get here, all models failed
        if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error:
            friendly_msg = "⚠️ تم تجاوز الحد اليومي لطلبات الذكاء الاصطناعي (Gemini Quota). يمكنك رؤية نتائج التحليل الموضعية أدناه، ولكن التوصيات الغذائية والمنتجات ستتوفر لاحقاً."
            return friendly_msg, []
            
        return "حدث خطأ بسيط أثناء تحضير التوصيات المخصصة. يرجى المحاولة لاحقاً.", []

    def _analyze_results(self, raw_result: dict, inference_time: float, age: str = None, skin_type: str = None) -> dict:
        """
        Analyze raw Roboflow results and produce a structured report.
        """
        predictions = raw_result.get("predictions", [])
        image_info = {
            "width": raw_result.get("image", {}).get("width", 0),
            "height": raw_result.get("image", {}).get("height", 0)
        }

        # Process each detection
        detections = []
        condition_counts = {}
        condition_max_confidence = {}

        for pred in predictions:
            cls = pred.get("class", "Unknown")
            conf = round(pred.get("confidence", 0) * 100, 1)

            condition_info = SKIN_CONDITIONS.get(cls, {})

            detection = {
                "class": cls,
                "confidence": conf,
                "bbox": {
                    "x": pred.get("x", 0),
                    "y": pred.get("y", 0),
                    "width": pred.get("width", 0),
                    "height": pred.get("height", 0)
                },
                "color": condition_info.get("color", "#FFFFFF"),
                "icon": condition_info.get("icon", "❓"),
                "severity": condition_info.get("severity", "unknown"),
                "description": condition_info.get("description", ""),
                "tips": condition_info.get("tips", []),
                "name_ar": condition_info.get("name_ar", cls)
            }
            detections.append(detection)

            # Track counts and max confidence per condition
            condition_counts[cls] = condition_counts.get(cls, 0) + 1
            if cls not in condition_max_confidence or conf > condition_max_confidence[cls]:
                condition_max_confidence[cls] = conf

        # Build summary
        total_detections = len(detections)
        unique_conditions = list(condition_counts.keys())

        # Calculate overall skin health score (Base 95 deduction system)
        severity_penalties = {
            "خفيف": 3.0,      # Mild
            "متوسط": 8.0,     # Moderate
            "شديد": 20.0,     # Severe
            "unknown": 5.0    # Fallback
        }
        
        if detections:
            total_penalty = 0
            for d in detections:
                # Deduction = severity_weight * confidence_factor
                conf_factor = d["confidence"] / 100.0
                penalty = severity_penalties.get(d["severity"], 5.0) * conf_factor
                total_penalty += penalty
            
            # Additional penalty for variety of conditions (diversity of issues)
            if len(unique_conditions) > 1:
                total_penalty += (len(unique_conditions) - 1) * 5
            
            # Calculate from base 95 so any issue reduces the score immediately
            health_score = max(5, int(95 - total_penalty))
        else:
            health_score = 95

        # Generate overall recommendation
        if health_score >= 80:
            overall_recommendation = "بشرتك تبدو صحية! حافظ على روتين العناية الحالي الخاص بك."
        elif health_score >= 60:
            overall_recommendation = "تم اكتشاف بعض المخاوف المتعلقة بالبشرة. فكري في تعديل روتين العناية الخاص بك."
        elif health_score >= 40:
            overall_recommendation = "تم اكتشاف عدة مشاكل في البشرة. يوصى باتباع روتين عناية متخصص."
        else:
            overall_recommendation = "تم اكتشاف مشاكل كبيرة في البشرة. يوصى باستشارة طبيب أمراض جلدية."

        # Aggregate tips by condition
        all_tips = {}
        for d in detections:
            if d["class"] not in all_tips:
                all_tips[d["class"]] = {
                    "tips": d["tips"],
                    "description": d["description"],
                    "count": condition_counts.get(d["class"], 1),
                    "max_confidence": condition_max_confidence.get(d["class"], 0),
                    "icon": d["icon"],
                    "color": d["color"],
                    "severity": d["severity"],
                    "name_ar": d.get("name_ar", d["class"])
                }

        # Generate Dynamic LLM Diet and Product Recommendations
        llm_diet_plan, recommended_products = self._generate_diet_and_products(unique_conditions, age, skin_type)

        result_id = str(uuid.uuid4())
        
        final_result = {
            "id": result_id,
            "success": True,
            "inference_time_ms": inference_time,
            "image": image_info,
            "total_detections": total_detections,
            "unique_conditions": len(unique_conditions),
            "conditions_found": unique_conditions,
            "health_score": health_score,
            "overall_recommendation": overall_recommendation,
            "detections": detections,
            "condition_summary": all_tips,
            "llm_diet_plan": llm_diet_plan,
            "recommended_products": recommended_products,
            "model_id": MODEL_ID,
            "summary": {
                "total": total_detections,
                "conditions": unique_conditions,
                "health_score": health_score
            }
        }
        
        # Cache the result for future feedback
        self.results_cache[result_id] = final_result
        return final_result

    def get_history(self) -> list:
        """Return detection history."""
        return self.detection_history

    def clear_history(self):
        """Clear detection history."""
        self.detection_history = []
        self.results_cache = {}

    def update_result_with_feedback(self, result_id: str, rating: int, comment: str) -> dict:
        """Add user feedback to an existing result and return the updated result."""
        if result_id not in self.results_cache:
            return None
        
        result = self.results_cache[result_id]
        result["user_feedback"] = {
            "rating": rating,
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        }
        
        # Also update history record if it exists (matching by result_id in a real app)
        # For simplicity, we just return the enriched result
        return result
