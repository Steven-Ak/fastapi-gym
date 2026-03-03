from groq import AsyncGroq
from app.core.config import settings
from fastapi import HTTPException
import json
import re

client = AsyncGroq(api_key=settings.GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"


async def _chat(system: str, user: str) -> str:
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content


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


async def generate_workout_plan(profile: dict) -> dict:
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

    raw = await _chat(system, user)

    try:
        return _parse_json(raw)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail=f"LLM returned invalid JSON: {raw[:300]}"
        )