"""
Skin Problem Detection Agent
Uses Roboflow's multi-class model via REST API to detect skin conditions.
"""

import os
import json
import base64
import time
import requests
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

    def _generate_diet_plan(self, unique_conditions: list, age: str = None, skin_type: str = None) -> str:
        """Call Gemini to generate a diet plan based on detected skin conditions and user profile."""
        if not self._llm:
            return "مفتاح API الخاص بـ Gemini مفقود في config.py. يرجى إضافته للحصول على خطة غذائية بالذكاء الاصطناعي."
        
        if not unique_conditions:
            return "لم يتم اكتشاف أي مشاكل جلدية. حافظ على نظامك الغذائي الصحي الحالي للحفاظ على نضارة بشرتك."

        condition_names = ", ".join(unique_conditions)
        
        # Build user profile string
        profile_parts = []
        if age:
            profile_parts.append(f"يبلغ من العمر {age} عاماً")
        if skin_type:
            profile_parts.append(f"نوع بشرته: {skin_type}")
            
        profile_context = ""
        if profile_parts:
            profile_context = f"معلومات المستخدم: {' و '.join(profile_parts)}."

        prompt = f"""
        يعاني المستخدم من الحالات الجلدية التالية: {condition_names}.
        {profile_context}
        بصفتك خبير تغذية وأمراض جلدية، قم بإعداد خطة غذائية موجزة (بين 2 إلى 4 نقاط كحد أقصى).
        اذكر الأطعمة التي ينصح بتناولها والأطعمة التي يجب تجنبها لتحسين هذه الحالات المحددة.
        يجب أن تكون التوصيات دقيقة وعلمية ومباشرة.
        اكتب باللغة العربية. استخدم التنسيق النقطي (Bullet points).
        لا تكتب مقدمات أو خاتمات طويلة، ادخل في صلب الموضوع فوراً.
        """
        
        try:
            response = self._llm.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {str(e)}"

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
                "tips": condition_info.get("tips", [])
            }
            detections.append(detection)

            # Track counts and max confidence per condition
            condition_counts[cls] = condition_counts.get(cls, 0) + 1
            if cls not in condition_max_confidence or conf > condition_max_confidence[cls]:
                condition_max_confidence[cls] = conf

        # Build summary
        total_detections = len(detections)
        unique_conditions = list(condition_counts.keys())

        # Calculate overall skin health score
        severity_scores = {"mild": 0.9, "moderate": 0.7, "severe": 0.4}
        if detections:
            avg_severity = sum(
                severity_scores.get(d["severity"], 0.5) for d in detections
            ) / len(detections)
            health_score = max(10, min(100, int(avg_severity * 100 - total_detections * 3)))
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
                    "severity": d["severity"]
                }

        # Generate Dynamic LLM Diet Plan
        llm_diet_plan = self._generate_diet_plan(unique_conditions, age, skin_type)

        return {
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
            "model_id": MODEL_ID,
            "summary": {
                "total": total_detections,
                "conditions": unique_conditions,
                "health_score": health_score
            }
        }

    def get_history(self) -> list:
        """Return detection history."""
        return self.detection_history

    def clear_history(self):
        """Clear detection history."""
        self.detection_history = []
