from fastapi import APIRouter, Depends

from backend.db import get_conn
from backend.auth_utils import get_current_user

from fitness_metrics import (
    workout_count_per_week, volume_load_per_session,
    weekly_hard_sets_per_muscle, estimated_1rm_trend, prs_this_month,
    daily_macros, calorie_adherence, protein_adherence,
    workout_adherence, food_logging_adherence,
    training_score, nutrition_score, consistency_score,
    load_sessions, load_sets_with_exercises,
)
from recommendations import generate_recommendations

router = APIRouter()


def _df_to_records(df):
    """Convert DataFrame to JSON-safe list of dicts."""
    if df.empty:
        return []
    out = df.copy()
    for col in out.columns:
        if hasattr(out[col].dtype, "name") and "datetime" in out[col].dtype.name:
            out[col] = out[col].astype(str)
        elif out[col].dtype == "object":
            out[col] = out[col].apply(lambda v: str(v) if hasattr(v, "isoformat") else v)
    return out.to_dict(orient="records")


@router.get("/workout-dashboard")
def workout_dashboard(user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        sessions = load_sessions(conn, user["username"], days=60)
        sets_df = load_sets_with_exercises(conn, user["username"], days=60)

    wc = workout_count_per_week(sessions, weeks=8)
    vl = volume_load_per_session(sets_df)
    hs = weekly_hard_sets_per_muscle(sets_df, weeks=4)

    exercise_names = sorted(sets_df["exercise_name"].unique().tolist()) if not sets_df.empty else []

    e1rm_data = {}
    for name in exercise_names:
        if sets_df.empty:
            continue
        ex_id = sets_df[sets_df["exercise_name"] == name]["exercise_id"].iloc[0]
        trend = estimated_1rm_trend(sets_df, exercise_id=int(ex_id))
        e1rm_data[name] = _df_to_records(trend)

    return {
        "weekly_count": _df_to_records(wc),
        "volume_trend": _df_to_records(vl),
        "hard_sets": _df_to_records(hs),
        "exercise_names": exercise_names,
        "e1rm_trends": e1rm_data,
    }


@router.get("/nutrition-dashboard")
def nutrition_dashboard(user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        dm = daily_macros(conn, user["username"], days=30)
        food_adh = food_logging_adherence(conn, user["username"], window=7)

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_goals WHERE user=%s", (user["username"],))
        goals = cursor.fetchone()

    cal_target = float(goals["calorie_target"]) if goals and goals["calorie_target"] else 0
    prot_target = float(goals["protein_target"]) if goals and goals["protein_target"] else 0

    cal_adh = calorie_adherence(dm, cal_target, window=7)
    prot_adh = protein_adherence(dm, prot_target, window=7)

    return {
        "daily_macros": _df_to_records(dm),
        "calorie_target": cal_target,
        "protein_target": prot_target,
        "calorie_adherence": cal_adh,
        "protein_adherence": prot_adh,
        "food_logging_adherence": food_adh,
    }


@router.get("/progress-dashboard")
def progress_dashboard(user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        sessions = load_sessions(conn, user["username"], days=60)
        sets_df = load_sets_with_exercises(conn, user["username"], days=60)
        dm = daily_macros(conn, user["username"], days=30)
        food_adh = food_logging_adherence(conn, user["username"], window=7)

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_goals WHERE user=%s", (user["username"],))
        goals = cursor.fetchone()

    goal_type = goals["goal_type"] if goals else "fat_loss"
    cal_target = float(goals["calorie_target"]) if goals and goals["calorie_target"] else 0
    prot_target = float(goals["protein_target"]) if goals and goals["protein_target"] else 0
    train_target = int(goals["training_days_per_week"]) if goals and goals["training_days_per_week"] else 4

    work_adh = workout_adherence(sessions, train_target, window_weeks=1)
    cal_adh = calorie_adherence(dm, cal_target, window=7)
    prot_adh = protein_adherence(dm, prot_target, window=7)
    hs = weekly_hard_sets_per_muscle(sets_df, weeks=1)

    t_score = training_score(work_adh, hs)
    n_score = nutrition_score(cal_adh, prot_adh, goal_type)
    c_score = consistency_score(work_adh, food_adh)

    prs = prs_this_month(sets_df)

    tips = generate_recommendations(
        goal_type=goal_type, daily_macros_df=dm,
        calorie_target=cal_target, protein_target=prot_target,
        sessions_df=sessions, training_days_target=train_target,
        hard_sets_df=hs,
    )

    return {
        "training_score": t_score,
        "nutrition_score": n_score,
        "consistency_score": c_score,
        "prs": _df_to_records(prs),
        "recommendations": tips,
        "goal_type": goal_type,
    }
