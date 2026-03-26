"""
V1 fitness metrics: workout volume, 1RM estimates, adherence scores,
and nutrition aggregates.  All functions accept a DB connection or
pre-fetched DataFrames and return plain dicts / DataFrames ready for
Plotly or Streamlit rendering.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso_week_label(dt):
    """Return 'YYYY-WNN' for a date."""
    iso = dt.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def epley_1rm(weight, reps):
    """Epley estimated 1-rep max.  Returns 0 for bodyweight (weight=0)."""
    if weight <= 0 or reps <= 0:
        return 0.0
    if reps == 1:
        return float(weight)
    return round(weight * (1 + reps / 30.0), 1)


# ---------------------------------------------------------------------------
# Workout metrics
# ---------------------------------------------------------------------------

def workout_count_per_week(df_sessions: pd.DataFrame, weeks: int = 8) -> pd.DataFrame:
    """Count of workout sessions per ISO week.

    Expects df_sessions with at least ``session_date`` (date/datetime).
    Returns DataFrame with columns ``week``, ``workouts``.
    """
    if df_sessions.empty:
        return pd.DataFrame(columns=["week", "workouts"])

    df = df_sessions.copy()
    df["session_date"] = pd.to_datetime(df["session_date"])
    cutoff = datetime.today() - timedelta(weeks=weeks)
    df = df[df["session_date"] >= cutoff]
    df["week"] = df["session_date"].apply(_iso_week_label)
    result = df.groupby("week").agg(workouts=("session_date", "nunique")).reset_index()
    return result.sort_values("week")


def volume_load_per_session(df_sets: pd.DataFrame) -> pd.DataFrame:
    """Total volume load (reps * weight) per session_id.

    Returns DataFrame: session_id, session_date, volume.
    """
    if df_sets.empty:
        return pd.DataFrame(columns=["session_id", "session_date", "volume"])

    df = df_sets.copy()
    df["vol"] = df["reps"] * df["weight"]
    result = df.groupby(["session_id", "session_date"]).agg(volume=("vol", "sum")).reset_index()
    return result.sort_values("session_date")


def weekly_hard_sets_per_muscle(df_sets: pd.DataFrame, weeks: int = 4) -> pd.DataFrame:
    """Count hard sets per muscle group per week.

    A set is 'hard' when RPE >= 7 or RIR <= 3.  If both are null the set is
    excluded.
    """
    if df_sets.empty:
        return pd.DataFrame(columns=["week", "muscle_group", "hard_sets"])

    df = df_sets.copy()
    df["session_date"] = pd.to_datetime(df["session_date"])
    cutoff = datetime.today() - timedelta(weeks=weeks)
    df = df[df["session_date"] >= cutoff]

    has_rpe = df["rpe"].notna()
    has_rir = df["rir"].notna()
    hard = ((has_rpe & (df["rpe"] >= 7)) | (has_rir & (df["rir"] <= 3)))
    df = df[hard]
    df["week"] = df["session_date"].apply(_iso_week_label)
    result = (
        df.groupby(["week", "muscle_group"])
        .size()
        .reset_index(name="hard_sets")
    )
    return result.sort_values(["week", "muscle_group"])


def estimated_1rm_trend(df_sets: pd.DataFrame, exercise_id: int | None = None) -> pd.DataFrame:
    """Session-max estimated 1RM per exercise over time.

    If *exercise_id* is given, filter to that exercise only.
    Returns: exercise_id, exercise_name, session_date, e1rm.
    """
    if df_sets.empty:
        return pd.DataFrame(columns=["exercise_id", "exercise_name", "session_date", "e1rm"])

    df = df_sets.copy()
    if exercise_id is not None:
        df = df[df["exercise_id"] == exercise_id]
    df["e1rm"] = df.apply(lambda r: epley_1rm(r["weight"], r["reps"]), axis=1)
    result = (
        df.groupby(["exercise_id", "exercise_name", "session_date"])
        .agg(e1rm=("e1rm", "max"))
        .reset_index()
    )
    return result.sort_values("session_date")


def prs_this_month(df_sets: pd.DataFrame) -> pd.DataFrame:
    """Best estimated 1RM per exercise in the current month vs previous month.

    Returns: exercise_name, current_1rm, previous_1rm, improvement.
    """
    if df_sets.empty:
        return pd.DataFrame(columns=["exercise_name", "current_1rm", "previous_1rm", "improvement"])

    df = df_sets.copy()
    df["session_date"] = pd.to_datetime(df["session_date"])
    df["e1rm"] = df.apply(lambda r: epley_1rm(r["weight"], r["reps"]), axis=1)

    today = datetime.today()
    cur_start = today.replace(day=1)
    prev_start = (cur_start - timedelta(days=1)).replace(day=1)

    cur = df[df["session_date"] >= cur_start].groupby("exercise_name")["e1rm"].max()
    prev = df[(df["session_date"] >= prev_start) & (df["session_date"] < cur_start)].groupby("exercise_name")["e1rm"].max()

    merged = pd.DataFrame({"current_1rm": cur, "previous_1rm": prev}).fillna(0)
    merged["improvement"] = merged["current_1rm"] - merged["previous_1rm"]
    merged = merged.reset_index()
    return merged[merged["current_1rm"] > 0].sort_values("improvement", ascending=False)


# ---------------------------------------------------------------------------
# Nutrition metrics
# ---------------------------------------------------------------------------

def daily_macros(conn, user: str, days: int = 30) -> pd.DataFrame:
    """Calories / protein / fat / carbs per day for the last *days* days."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT fi.date,
               ROUND(SUM(COALESCE(fi.quantity * fo.calories, fi.calories, 0)), 1) AS calories,
               ROUND(SUM(COALESCE(fi.quantity * fo.protein,  fi.protein,  0)), 1) AS protein,
               ROUND(SUM(COALESCE(fi.quantity * fo.fat,      fi.fat,      0)), 1) AS fat,
               ROUND(SUM(COALESCE(fi.quantity * fo.carbs,    fi.carbs,    0)), 1) AS carbs
        FROM food_intake fi
        LEFT JOIN food_items fo ON fi.food_id = fo.id
        WHERE fi.user = %s AND fi.date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        GROUP BY fi.date
        ORDER BY fi.date
    """, (user, days))
    rows = cursor.fetchall()
    cursor.close()
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["date", "calories", "protein", "fat", "carbs"])


def calorie_adherence(daily_df: pd.DataFrame, target: float, window: int = 7) -> float:
    """Fraction of days in the last *window* where calories are within ±10% of target."""
    if daily_df.empty or target <= 0:
        return 0.0
    recent = daily_df.tail(window)
    within = ((recent["calories"] >= target * 0.9) & (recent["calories"] <= target * 1.1)).sum()
    return round(within / min(window, len(recent)), 2)


def protein_adherence(daily_df: pd.DataFrame, target: float, window: int = 7) -> float:
    """Fraction of days in the last *window* where protein meets target."""
    if daily_df.empty or target <= 0:
        return 0.0
    recent = daily_df.tail(window)
    met = (recent["protein"] >= target).sum()
    return round(met / min(window, len(recent)), 2)


# ---------------------------------------------------------------------------
# Adherence / consistency
# ---------------------------------------------------------------------------

def workout_adherence(df_sessions: pd.DataFrame, target_days: int, window_weeks: int = 1) -> float:
    """Fraction of target training days met in the last *window_weeks*."""
    if df_sessions.empty or target_days <= 0:
        return 0.0
    cutoff = datetime.today() - timedelta(weeks=window_weeks)
    df = df_sessions.copy()
    df["session_date"] = pd.to_datetime(df["session_date"])
    count = df[df["session_date"] >= cutoff]["session_date"].nunique()
    return round(min(count / target_days, 1.0), 2)


def food_logging_adherence(conn, user: str, window: int = 7) -> float:
    """Fraction of the last *window* days that have at least one food log."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(DISTINCT date)
        FROM food_intake
        WHERE user = %s AND date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
    """, (user, window))
    count = cursor.fetchone()[0]
    cursor.close()
    return round(count / window, 2)


def combined_adherence(workout_adh: float, food_adh: float) -> float:
    return round((workout_adh + food_adh) / 2, 2)


# ---------------------------------------------------------------------------
# Composite scores  (0-100)
# ---------------------------------------------------------------------------

def training_score(workout_adh: float, hard_sets_df: pd.DataFrame, target_sets: int = 10) -> int:
    """Blend workout adherence and hard-set volume into 0-100."""
    adh_part = workout_adh * 50
    if hard_sets_df.empty:
        sets_part = 0
    else:
        total = hard_sets_df["hard_sets"].sum()
        sets_part = min(total / max(target_sets, 1), 1.0) * 50
    return int(round(adh_part + sets_part))


def nutrition_score(cal_adh: float, prot_adh: float, goal_type: str = "fat_loss") -> int:
    """Blend calorie and protein adherence with goal-specific weights."""
    weights = {
        "fat_loss": (0.6, 0.4),
        "muscle_gain": (0.3, 0.7),
        "recomposition": (0.5, 0.5),
    }
    cw, pw = weights.get(goal_type, (0.5, 0.5))
    return int(round((cal_adh * cw + prot_adh * pw) * 100))


def consistency_score(workout_adh: float, food_adh: float) -> int:
    return int(round(combined_adherence(workout_adh, food_adh) * 100))


# ---------------------------------------------------------------------------
# Data loaders (fetch from DB into DataFrames used by above functions)
# ---------------------------------------------------------------------------

def load_sessions(conn, user: str, days: int = 60) -> pd.DataFrame:
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, user, session_date, notes
        FROM workout_sessions
        WHERE user = %s AND session_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        ORDER BY session_date
    """, (user, days))
    rows = cursor.fetchall()
    cursor.close()
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["id", "user", "session_date", "notes"])


def load_sets_with_exercises(conn, user: str, days: int = 60) -> pd.DataFrame:
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT es.id, es.session_id, ws.session_date, es.exercise_id,
               ex.name AS exercise_name, ex.muscle_group,
               es.set_order, es.reps, es.weight, es.rpe, es.rir
        FROM exercise_sets es
        JOIN workout_sessions ws ON es.session_id = ws.id
        JOIN exercises ex ON es.exercise_id = ex.id
        WHERE ws.user = %s AND ws.session_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        ORDER BY ws.session_date, es.session_id, es.set_order
    """, (user, days))
    rows = cursor.fetchall()
    cursor.close()
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["id", "session_id", "session_date", "exercise_id",
                 "exercise_name", "muscle_group", "set_order", "reps",
                 "weight", "rpe", "rir"]
    )
