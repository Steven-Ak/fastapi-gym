from app.database import supabase
from datetime import datetime
import uuid


async def save_workout_plan(member_id: str, plan_json: dict) -> str:
    # deactivate existing active plan first
    supabase.table("workout_plans") \
        .update({"is_active": False}) \
        .eq("member_id", member_id) \
        .eq("is_active", True) \
        .execute()

    plan_id = str(uuid.uuid4())
    supabase.table("workout_plans").insert({
        "id": plan_id,
        "member_id": member_id,
        "plan_json": plan_json,
        "week_number": 1,
        "is_active": True,
        "adapted_from_id": None,
        "generated_at": datetime.utcnow().isoformat(),
    }).execute()
    return plan_id


async def get_active_workout_plan(member_id: str) -> dict | None:
    result = supabase.table("workout_plans") \
        .select("*") \
        .eq("member_id", member_id) \
        .eq("is_active", True) \
        .execute()
    return result.data[0] if result.data else None


async def upsert_profile(member_id: str, data: dict):
    existing = supabase.table("member_profiles") \
        .select("id") \
        .eq("member_id", member_id) \
        .execute()

    if existing.data:
        supabase.table("member_profiles") \
            .update({**data, "updated_at": datetime.utcnow().isoformat()}) \
            .eq("member_id", member_id) \
            .execute()
    else:
        supabase.table("member_profiles").insert({
            "id": str(uuid.uuid4()),
            "member_id": member_id,
            **data
        }).execute()


async def get_profile(member_id: str) -> dict | None:
    result = supabase.table("member_profiles") \
        .select("*") \
        .eq("member_id", member_id) \
        .execute()
    return result.data[0] if result.data else None