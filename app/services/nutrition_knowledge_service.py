"""
NutritionKnowledge — local RAG context builder for nutrition plan generation.
Uses hardcoded knowledge until pgvector is fully seeded.
"""


class NutritionKnowledge:

    def calculate_calories(
        self, weight_kg: float, height_cm: float, goal: str
    ) -> int:
        # Mifflin-St Jeor BMR (assuming moderate activity)
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * 25 + 5
        tdee = bmr * 1.55  # moderate activity

        if goal == "lose_weight":
            return int(tdee - 500)
        elif goal in ("gain_weight", "build_muscle"):
            return int(tdee + 300)
        else:
            return int(tdee)

    def build_rag_context(
        self,
        goal: str,
        weight_kg: float,
        height_cm: float,
        diseases: str | None,
        allergies: str | None,
        calorie_target: int,
    ) -> str:
        lines = [
            f"الهدف: {goal}",
            f"الوزن: {weight_kg} كجم | الطول: {height_cm} سم",
            f"هدف السعرات اليومية: {calorie_target} سعرة",
        ]

        if diseases:
            lines.append(f"الحالات الصحية: {diseases}")
        if allergies:
            lines.append(f"الحساسية الغذائية: {allergies}")

        goal_tips = {
            "lose_weight":     "بروتين عالي، كربوهيدرات منخفضة، تجنب السكريات والمقليات.",
            "gain_weight":     "سعرات عالية، وجبات كل 2-3 ساعات، بروتين + كربوهيدرات معاً.",
            "build_muscle":    "1.6-2.2 جم بروتين لكل كجم، كربوهيدرات قبل وبعد التمرين.",
            "maintain_weight": "توازن الماكروز، تنويع المصادر الغذائية، نشاط بدني منتظم.",
        }
        tip = goal_tips.get(goal, "")
        if tip:
            lines.append(f"نصائح: {tip}")

        disease_tips = {
            "hypertension":   "تجنب الملح والأطعمة المعلبة، زد البوتاسيوم والمغنيسيوم.",
            "diabetes":       "كربوهيدرات معقدة فقط، تجنب السكريات، وجبات صغيرة متكررة.",
            "cholesterol":    "تجنب الدهون المشبعة، زد الألياف والأوميغا 3.",
        }
        if diseases:
            for key, tip in disease_tips.items():
                if key in (diseases or "").lower():
                    lines.append(f"تعليمات طبية: {tip}")

        return "\n".join(lines)