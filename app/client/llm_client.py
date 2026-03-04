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
        
    # These methods are to be added inside the GroqLLMClient class in llm_client.py
# Ensure `import json` is at the top of llm_client.py (it already is)

    async def answer_exercise_question(
        self,
        question: str,
        context: str,
        injuries: str | None = None,
        diseases: str | None = None,
    ) -> str:
        """
        Answer an Arabic exercise question using retrieved RAG context.
        Returns a plain Arabic string (not JSON).
        """
        health_note = ""
        if injuries:
            health_note += f"\nالعضو لديه الإصابات التالية: {injuries}"
        if diseases:
            health_note += f"\nالعضو لديه الأمراض التالية: {diseases}"
        if health_note:
            health_note = "\n\nمعلومات صحية مهمة عن العضو:" + health_note + \
                          "\nراعِ هذه المعلومات في إجابتك وتجنب اقتراح تمارين قد تضر بحالته."

        system = """أنت مدرب لياقة بدنية خبير ومتخصص في الإجابة على أسئلة التمارين الرياضية.
أجب دائماً باللغة العربية بأسلوب واضح ومفيد.
عند الإجابة، ركز على التمارين التي تستهدف العضلة أو المنطقة المذكورة في السؤال بشكل مباشر.
استخدم حقل "العضلات المستهدفة" في السياق لتحديد التمارين الأنسب.
إذا لم يكن في السياق تمرين مباشر للمنطقة المطلوبة، قل ذلك بوضوح ولا تقترح تمارين لعضلات مختلفة.
إذا كانت هناك إصابات أو أمراض، تأكد من مراعاتها في إجابتك."""

        user = f"""سؤال العضو: {question}{health_note}

السياق المسترجع من قاعدة بيانات التمارين:
{context}

أجب على سؤال العضو بشكل مفصل ومفيد بالعربية."""

        return await self._chat(system, user, json_mode=False)
    async def generate_arabic_keywords(self, exercises: list[dict]) -> list[str]:
        """
        Given a batch of exercises, return a list of Arabic keyword strings —
        one per exercise — to enrich embedding for Arabic query matching.
        Batched as a single LLM call for efficiency.
        """
        batch_input = []
        for ex in exercises:
            batch_input.append({
                "id": ex.get("exercise_id"),
                "name": ex.get("name"),
                "name_ar": ex.get("name_ar"),
                "type": ex.get("exercise_type"),
                "targets": ex.get("target_muscle", []),
                "secondary": ex.get("secondary_muscles", []),
                "tags": ex.get("tags", []),
            })

        system = """أنت خبير لياقة بدنية. مهمتك توليد كلمات مفتاحية عربية غنية لكل تمرين.
أجب فقط بـ JSON صحيح — مصفوفة بنفس ترتيب المدخلات.
لكل تمرين أنتج: اسم عربي بديل، أسماء العضلات بالعربي، نوع التمرين بالعربي، مرادفات بحث شائعة.
المخرجات يجب أن تساعد في البحث بالعربية العامية والفصحى معاً."""

        user = f"""أنتج كلمات مفتاحية عربية للتمارين التالية:
{json.dumps(batch_input, ensure_ascii=False)}

أرجع JSON بهذا الشكل بالضبط — مصفوفة strings فقط، بدون أي نص إضافي:
[
  "كلمات مفتاحية للتمرين الأول مفصولة بمسافات أو فاصلة",
  "كلمات مفتاحية للتمرين الثاني",
  ...
]"""

        raw = await self._chat(system, user, json_mode=True)
        try:
            parsed = self._parse_json(raw)
            # Handle both direct list or wrapped object
            if isinstance(parsed, list):
                return [str(k) for k in parsed]
            # Some models wrap it: {"keywords": [...]}
            for v in parsed.values():
                if isinstance(v, list):
                    return [str(k) for k in v]
        except Exception:
            pass
        # Fallback: return empty strings so seeding never fails
        return [""] * len(exercises)