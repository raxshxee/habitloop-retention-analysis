import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


RAW_PATH = Path("data/raw_reviews.csv")
ENRICHED_PATH = Path("data/enriched_reviews.csv")
COMPACT_CSV_PATH = Path("data/retention_review_log_compact.csv")
COMPACT_XLSX_PATH = Path("data/retention_review_log_compact.xlsx")
SUMMARY_PATH = Path("data/summary.json")
DASHBOARD_TEMPLATE_PATH = Path("dashboard_template.html")
DASHBOARD_PATH = Path("dashboard.html")


THEMES = {
    "Onboarding friction": ["confusing", "setup", "sign up", "login", "tutorial", "beginner", "overwhelming"],
    "Habit break / streak loss": ["streak", "lost progress", "progress gone", "habit", "daily", "missed", "routine"],
    "Pricing / subscription concern": ["price", "expensive", "subscription", "premium", "paywall", "charged", "billing", "refund", "free trial", "cancel"],
    "Feature request": ["please add", "wish", "feature", "would like", "should have", "need", "missing", "customize", "option"],
    "Bug / reliability": ["bug", "crash", "glitch", "not working", "doesn't work", "freezes", "loading", "broken", "error", "lag"],
    "Notification / reminder issue": ["notification", "remind", "alert", "too many", "spam", "push", "email", "message"],
    "Support / trust issue": ["support", "customer service", "scam", "trust", "privacy", "contact", "response", "help", "account"],
    "Motivation / content fatigue": ["boring", "repetitive", "same", "tired", "content", "lessons", "too easy", "too hard", "annoying"],
    "Positive habit value": ["love", "helpful", "amazing", "great", "best", "life changing", "recommend", "fun", "motivated", "use every day"],
}

POSITIVE_WORDS = {"love", "loved", "great", "excellent", "amazing", "helpful", "best", "easy", "fun", "useful", "recommend", "perfect", "awesome", "motivating", "beautiful", "worth"}
NEGATIVE_WORDS = {"bad", "terrible", "awful", "hate", "expensive", "broken", "bug", "crash", "annoying", "confusing", "frustrating", "disappointed", "refund", "cancel", "scam", "boring", "useless", "problem", "issue", "glitch"}


def clean_text(value):
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def tokenize(text):
    return re.findall(r"[a-z']+", text.lower())


def classify_theme(text, rating):
    haystack = text.lower()
    scores = {theme: sum(1 for keyword in keywords if keyword in haystack) for theme, keywords in THEMES.items()}
    best_theme, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score > 0:
        return best_theme
    if rating >= 4:
        return "Positive habit value"
    if rating <= 2:
        return "Unspecified churn risk"
    return "General feedback"


def sentiment_score(text, rating):
    words = tokenize(text)
    lexical = 0 if not words else (sum(w in POSITIVE_WORDS for w in words) - sum(w in NEGATIVE_WORDS for w in words)) / math.sqrt(len(words))
    rating_signal = (rating - 3) / 2
    return round(max(-1, min(1, (lexical * 0.45) + (rating_signal * 0.55))), 3)


def lifecycle_stage(theme):
    mapping = {
        "Onboarding friction": "Activation",
        "Habit break / streak loss": "Engagement",
        "Notification / reminder issue": "Engagement",
        "Motivation / content fatigue": "Engagement",
        "Pricing / subscription concern": "Monetization / Save",
        "Support / trust issue": "Save",
        "Bug / reliability": "Save",
        "Feature request": "Expansion",
        "Positive habit value": "Advocacy",
        "Unspecified churn risk": "Save",
        "General feedback": "Engagement",
    }
    return mapping.get(theme, "Engagement")


def risk_level(rating, sentiment, theme):
    high_risk_themes = {"Pricing / subscription concern", "Bug / reliability", "Support / trust issue", "Unspecified churn risk"}
    if rating <= 2 and (theme in high_risk_themes or sentiment < -0.35):
        return "High"
    if rating <= 3 or sentiment < -0.15:
        return "Medium"
    return "Low"


def campaign_recommendations(theme):
    recommendations = {
        "Onboarding friction": ("First-session clarity sequence", "New user completes signup but has low early activity", "Show the first useful win, reduce setup anxiety, and make the next action feel obvious."),
        "Habit break / streak loss": ("Streak recovery and fresh-start flow", "User misses 1-3 expected usage days", "Normalize the lapse, protect identity, and offer a lightweight restart path."),
        "Pricing / subscription concern": ("Value proof before renewal", "Trial midpoint, renewal window, or cancellation intent", "Connect paid features to outcomes already experienced by the user."),
        "Bug / reliability": ("Trust repair service message", "Negative support or reliability signal", "Acknowledge friction, explain the fix, and reduce fear of wasted effort."),
        "Notification / reminder issue": ("Reminder preference reset", "Muted reminders, notification complaint, or declining sessions", "Let users choose cadence and tone instead of pushing generic reminders."),
        "Support / trust issue": ("Billing and account reassurance flow", "Refund, cancellation, privacy, or account support keywords", "Lead with control, transparency, and fast routes to human help."),
        "Motivation / content fatigue": ("Content variety and challenge refresh", "Repeated sessions with declining completion or boredom language", "Introduce novelty, choice, and difficulty calibration."),
        "Feature request": ("Feedback-to-roadmap loop", "Repeated requests for the same missing capability", "Make customers feel heard and invite them into beta or education moments."),
        "Positive habit value": ("Advocacy and referral prompt", "High rating plus strong positive habit language", "Ask for share or referral after users describe a meaningful outcome."),
    }
    campaign, trigger, message = recommendations.get(theme, ("Lifecycle education nudge", "General engagement signal", "Use customer language to clarify the next best action."))
    return {"campaign": campaign, "trigger": trigger, "message": message}


def top_examples(df, theme, limit=2):
    subset = df[df["theme"] == theme].copy()
    if subset.empty:
        return []
    subset["quote_score"] = subset["review_text"].str.len().clip(0, 350) + (5 - subset["rating"]) * 25
    subset = subset.sort_values(["rating", "quote_score"], ascending=[True, False])
    examples = []
    for _, row in subset.head(limit).iterrows():
        text = row["review_text"]
        if len(text) > 260:
            text = text[:257].rsplit(" ", 1)[0] + "..."
        examples.append({"app": row["app_name"], "rating": int(row["rating"]), "quote": text, "title": row["review_title"]})
    return examples


def build_app_summaries(df):
    summaries = []
    total_theme_share = df["theme"].value_counts(normalize=True)
    for app_name, app_df in df.groupby("app_name"):
        theme_counts = app_df["theme"].value_counts()
        stage_counts = app_df["lifecycle_stage"].value_counts()
        top_theme = theme_counts.index[0]
        app_theme_share = theme_counts / len(app_df)
        over_index = ((app_theme_share - total_theme_share.reindex(app_theme_share.index).fillna(0)) * 100).sort_values(ascending=False)
        summaries.append(
            {
                "app": app_name,
                "category": app_df["category"].iloc[0],
                "competitive_set": app_df["competitive_set"].iloc[0],
                "reviews": int(len(app_df)),
                "average_rating": round(float(app_df["rating"].mean()), 2),
                "medium_high_risk_share": round(float(app_df["risk_level"].isin(["Medium", "High"]).mean() * 100), 1),
                "top_signal": top_theme,
                "top_signal_share": round(float(theme_counts.iloc[0] / len(app_df) * 100), 1),
                "top_stage": stage_counts.index[0],
                "over_indexes_on": [
                    {"theme": theme, "points_above_benchmark": round(float(points), 1)}
                    for theme, points in over_index.head(3).items()
                ],
            }
        )
    return summaries


def build_category_summaries(df):
    summaries = []
    for category, category_df in df.groupby("category"):
        app_count = category_df["app_name"].nunique()
        risk_by_app = (
            category_df.assign(is_risk=category_df["risk_level"].isin(["Medium", "High"]))
            .groupby("app_name")["is_risk"]
            .mean()
            .sort_values(ascending=False)
        )
        top_themes = category_df["theme"].value_counts(normalize=True).mul(100).round(1).head(3)
        summaries.append(
            {
                "category": category,
                "competitive_set": category_df["competitive_set"].iloc[0],
                "apps": sorted(category_df["app_name"].unique().tolist()),
                "reviews": int(len(category_df)),
                "app_count": int(app_count),
                "highest_risk_app": risk_by_app.index[0],
                "highest_risk_share": round(float(risk_by_app.iloc[0] * 100), 1),
                "top_signals": [{"theme": theme, "share": float(share)} for theme, share in top_themes.items()],
            }
        )
    return summaries


def build_cross_app_patterns(df):
    app_count = df["app_name"].nunique()
    theme_app_presence = df.groupby("theme")["app_name"].nunique().sort_values(ascending=False)
    common_themes = [theme for theme, count in theme_app_presence.items() if count == app_count]
    risk_by_app = (
        df.assign(is_risk=df["risk_level"].isin(["Medium", "High"]))
        .groupby("app_name")["is_risk"]
        .mean()
        .sort_values(ascending=False)
    )
    stage_matrix = (
        pd.crosstab(df["app_name"], df["lifecycle_stage"], normalize="index")
        .mul(100)
        .round(1)
        .to_dict(orient="index")
    )
    theme_matrix = (
        pd.crosstab(df["app_name"], df["theme"], normalize="index")
        .mul(100)
        .round(1)
        .to_dict(orient="index")
    )
    return {
        "why_these_apps": (
            "The apps are arranged as competitive pairs inside four retention-heavy categories: language learning, "
            "meditation and sleep, self-care journaling, and routine building. That makes the dashboard a category "
            "benchmark instead of a random review sorter: each pair reveals shared pain points and app-specific gaps."
        ),
        "common_themes": common_themes[:8],
        "highest_risk_app": {
            "app": risk_by_app.index[0],
            "medium_high_risk_share": round(float(risk_by_app.iloc[0] * 100), 1),
        },
        "stage_matrix": stage_matrix,
        "theme_matrix": theme_matrix,
    }


def write_compact_logs(df):
    compact = df[
        [
            "app_name",
            "category",
            "competitive_set",
            "rating",
            "updated",
            "review_title",
            "theme",
            "lifecycle_stage",
            "risk_level",
            "sentiment",
            "review_text",
        ]
    ].copy()
    compact["review_text"] = compact["review_text"].str.slice(0, 320)
    compact = compact.rename(
        columns={
            "app_name": "app",
            "updated": "review_date",
            "review_title": "title",
            "lifecycle_stage": "stage",
            "risk_level": "risk",
            "review_text": "review_excerpt",
        }
    )
    compact.to_csv(COMPACT_CSV_PATH, index=False, encoding="utf-8")
    compact.to_excel(COMPACT_XLSX_PATH, index=False)


def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError("Run scripts/1_collect_reviews.py first.")

    df = pd.read_csv(RAW_PATH)
    df["review_title"] = df["review_title"].apply(clean_text)
    df["review_text"] = df["review_text"].apply(clean_text)
    if "category" not in df.columns:
        df["category"] = "Habit app benchmark"
    if "competitive_set" not in df.columns:
        df["competitive_set"] = "Habit app benchmark"
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0).astype(int)
    df["vote_count"] = pd.to_numeric(df["vote_count"], errors="coerce").fillna(0).astype(int)
    df["combined_text"] = (df["review_title"] + " " + df["review_text"]).str.strip()

    df["theme"] = df.apply(lambda row: classify_theme(row["combined_text"], row["rating"]), axis=1)
    df["sentiment"] = df.apply(lambda row: sentiment_score(row["combined_text"], row["rating"]), axis=1)
    df["lifecycle_stage"] = df["theme"].apply(lifecycle_stage)
    df["risk_level"] = df.apply(lambda row: risk_level(row["rating"], row["sentiment"], row["theme"]), axis=1)
    df.to_csv(ENRICHED_PATH, index=False, encoding="utf-8")
    write_compact_logs(df)

    theme_counts = Counter(df["theme"])
    stage_counts = Counter(df["lifecycle_stage"])
    risk_counts = Counter(df["risk_level"])
    app_counts = Counter(df["app_name"])
    by_app_theme = defaultdict(dict)
    for (app, theme), count in df.groupby(["app_name", "theme"]).size().items():
        by_app_theme[app][theme] = int(count)

    campaigns = []
    for theme, count in theme_counts.most_common():
        rec = campaign_recommendations(theme)
        campaigns.append({
            "theme": theme,
            "count": int(count),
            "share": round(count / len(df) * 100, 1),
            "stage": lifecycle_stage(theme),
            "campaign": rec["campaign"],
            "trigger": rec["trigger"],
            "message": rec["message"],
            "examples": top_examples(df, theme, 2),
        })

    summary = {
        "project": "HabitLoop Retention Intelligence",
        "generated_from": "Apple public App Store review feeds",
        "total_reviews": int(len(df)),
        "apps": dict(app_counts),
        "categories": dict(Counter(df["category"])),
        "competitive_sets": {
            category: sorted(group["app_name"].unique().tolist())
            for category, group in df.groupby("category")
        },
        "average_rating": round(float(df["rating"].mean()), 2),
        "negative_review_share": round(float((df["rating"] <= 2).mean() * 100), 1),
        "medium_high_risk_share": round(float(df["risk_level"].isin(["Medium", "High"]).mean() * 100), 1),
        "theme_counts": dict(theme_counts.most_common()),
        "stage_counts": dict(stage_counts.most_common()),
        "risk_counts": dict(risk_counts),
        "by_app_theme": by_app_theme,
        "app_summaries": build_app_summaries(df),
        "category_summaries": build_category_summaries(df),
        "cross_app_patterns": build_cross_app_patterns(df),
        "campaigns": campaigns,
        "quotes": [
            {
                "app": row["app_name"],
                "category": row["category"],
                "competitive_set": row["competitive_set"],
                "rating": int(row["rating"]),
                "theme": row["theme"],
                "stage": row["lifecycle_stage"],
                "risk": row["risk_level"],
                "title": row["review_title"],
                "text": row["review_text"][:420],
            }
            for _, row in df.sort_values(["rating", "sentiment"]).head(24).iterrows()
        ],
        "reviews": [
            {
                "app": row["app_name"],
                "category": row["category"],
                "competitive_set": row["competitive_set"],
                "rating": int(row["rating"]),
                "theme": row["theme"],
                "stage": row["lifecycle_stage"],
                "risk": row["risk_level"],
                "sentiment": float(row["sentiment"]),
                "title": row["review_title"],
                "text": row["review_text"][:420],
            }
            for _, row in df.sort_values(["app_name", "rating", "sentiment"]).iterrows()
        ],
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    template = DASHBOARD_TEMPLATE_PATH.read_text(encoding="utf-8")
    DASHBOARD_PATH.write_text(template.replace("__DATA_JSON__", json.dumps(summary, ensure_ascii=False)), encoding="utf-8")

    print(f"Wrote {ENRICHED_PATH}")
    print(f"Wrote {COMPACT_CSV_PATH}")
    print(f"Wrote {COMPACT_XLSX_PATH}")
    print(f"Wrote {SUMMARY_PATH}")
    print(f"Wrote {DASHBOARD_PATH}")


if __name__ == "__main__":
    main()
