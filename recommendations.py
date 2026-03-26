"""
Rule-based recommendation engine for Fitness Tracker V1.

Each rule inspects 7–14 days of rolling metrics and the user's goal_type,
then returns a short actionable tip if triggered.
"""

from __future__ import annotations
import pandas as pd
from datetime import datetime, timedelta


def generate_recommendations(
    goal_type: str,
    daily_macros_df: pd.DataFrame,
    calorie_target: float,
    protein_target: float,
    sessions_df: pd.DataFrame,
    training_days_target: int,
    hard_sets_df: pd.DataFrame,
) -> list[dict]:
    """Return a list of ``{category, message}`` dicts — one per triggered rule."""
    tips: list[dict] = []

    # --- Protein ---
    if not daily_macros_df.empty and protein_target > 0:
        recent = daily_macros_df.tail(7)
        days_under = (recent["protein"] < protein_target).sum()
        if days_under >= 3:
            tips.append({
                "category": "Protein",
                "message": (
                    f"You missed your protein target on {days_under} of the last "
                    f"{len(recent)} days. Try adding a high-protein snack (Greek yogurt, "
                    f"whey shake, or eggs) to close the gap."
                ),
            })

    # --- Calories (goal-aware) ---
    if not daily_macros_df.empty and calorie_target > 0:
        recent = daily_macros_df.tail(7)
        avg_cal = recent["calories"].mean()
        if goal_type == "fat_loss" and avg_cal > calorie_target * 1.1:
            overshoot = int(avg_cal - calorie_target)
            tips.append({
                "category": "Calories",
                "message": (
                    f"You're averaging ~{overshoot} kcal above your target this week. "
                    f"Consider swapping calorie-dense sides for vegetables or reducing "
                    f"cooking oil by a tablespoon (~120 kcal)."
                ),
            })
        elif goal_type == "muscle_gain" and avg_cal < calorie_target * 0.9:
            deficit = int(calorie_target - avg_cal)
            tips.append({
                "category": "Calories",
                "message": (
                    f"You're about {deficit} kcal below your surplus target. "
                    f"Add a calorie-dense but clean snack — a handful of nuts or "
                    f"a banana with peanut butter."
                ),
            })

    # --- Workout consistency ---
    if training_days_target > 0:
        cutoff = datetime.today() - timedelta(days=7)
        if not sessions_df.empty:
            recent_sessions = sessions_df[
                pd.to_datetime(sessions_df["session_date"]) >= cutoff
            ]
            count = recent_sessions["session_date"].nunique()
        else:
            count = 0
        if count < training_days_target:
            remaining = training_days_target - count
            tips.append({
                "category": "Workout consistency",
                "message": (
                    f"You've trained {count} time(s) this week but your target is "
                    f"{training_days_target}. Schedule {remaining} more session(s) "
                    f"to stay on track."
                ),
            })

    # --- Hard sets per muscle group ---
    if not hard_sets_df.empty:
        this_week = hard_sets_df
        if "week" in this_week.columns:
            latest_week = this_week["week"].max()
            this_week = this_week[this_week["week"] == latest_week]
        low_groups = this_week[this_week["hard_sets"] < 6]
        if not low_groups.empty:
            groups = ", ".join(low_groups["muscle_group"].unique())
            tips.append({
                "category": "Volume",
                "message": (
                    f"Your hard-set count is low for: {groups}. "
                    f"Aim for 6–10 hard sets per muscle group per week for "
                    f"optimal stimulus."
                ),
            })

    # --- Goal-specific extras ---
    if goal_type == "recomposition":
        tips.append({
            "category": "Tracking",
            "message": (
                "For recomposition, tracking bodyweight and waist measurements "
                "weekly helps you see progress even when the scale doesn't move. "
                "Log them under Body Progress."
            ),
        })

    if not tips:
        tips.append({
            "category": "Keep it up!",
            "message": "You're on track across all metrics this week. Stay consistent!",
        })

    return tips
