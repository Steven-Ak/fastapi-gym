import json
import re

from groq import AsyncGroq

from app.core.config import settings
from app.core.exceptions import ExternalServiceError


class GroqLLMClient:
    """Concrete LLM client backed by Groq / Llama."""

    def __init__(self, api_key: str | None = None, model: str = "llama-3.3-70b-versatile"):
        self._client = AsyncGroq(api_key=api_key or settings.GROQ_API_KEY)
        self._model = model

    async def _chat(self, system: str, user: str, *, json_mode: bool = False) -> str:
        kwargs: dict = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = await self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    @staticmethod
    def _parse_json(raw: str) -> dict:
        text = raw.strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()

        if not text.startswith("{"):
            m = re.search(r"\{.*\}", text, flags=re.S)
            if m:
                text = m.group(0)

        return json.loads(text)

    

    async def generate_workout_plan(self, profile: dict) -> dict:
        system = """أنت مدرب لياقة بدنية محترف. أنشئ خطة تدريب مخصصة باللغة العربية.
أجب فقط بـ JSON صحيح بدون أي نص إضافي."""

        user = f"""أنشئ خطة تدريب 4 أسابيع للعضو:
- الهدف: {profile.get('goal')}
- المستوى: {profile.get('level')}
- أيام التدريب: {profile.get('days_per_week')} أيام/أسبوع
- الوزن: {profile.get('weight_kg')} كجم | الطول: {profile.get('height_cm')} سم
- الإصابات: {profile.get('injuries') or 'لا يوجد'}
- الأمراض: {profile.get('diseases') or 'لا يوجد'}

أرجع JSON بهذا الشكل:
{{
  "weeks": [
    {{
      "week": 1,
      "days": [
        {{
          "day": "الأحد",
          "focus": "الصدر والترايسبس",
          "exercises": [
            {{"name": "اسم التمرين", "sets": 3, "reps": "12", "rest_seconds": 60, "notes": "ملاحظة"}}
          ]
        }}
      ]
    }}
  ],
  "general_tips": ["نصيحة 1", "نصيحة 2"]
}}"""

        raw = await self._chat(system, user, json_mode=True)

        try:
            return self._parse_json(raw)
        except Exception:
            raise ExternalServiceError(detail=f"LLM returned invalid JSON: {raw[:300]}")

LLMClient = GroqLLMClient
