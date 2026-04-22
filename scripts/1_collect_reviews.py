import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


COUNTRY = "us"
PAGES_PER_APP = 10
OUTPUT_PATH = Path("data/raw_reviews.csv")

APPS = [
    {"name": "Duolingo", "app_id": "570060128", "category": "Language learning", "competitive_set": "Duolingo vs Babbel"},
    {"name": "Babbel - Language Learning", "app_id": "829587759", "category": "Language learning", "competitive_set": "Duolingo vs Babbel"},
    {"name": "Headspace: Meditation & Sleep", "app_id": "493145008", "category": "Meditation and sleep", "competitive_set": "Headspace vs Calm"},
    {"name": "Calm", "app_id": "571800810", "category": "Meditation and sleep", "competitive_set": "Headspace vs Calm"},
    {"name": "Finch: Self-Care Pet", "app_id": "1528595748", "category": "Self-care journaling", "competitive_set": "Finch vs Daylio"},
    {"name": "Daylio Journal - Mood Tracker", "app_id": "1194023242", "category": "Self-care journaling", "competitive_set": "Finch vs Daylio"},
    {"name": "Fabulous: Daily Habit Tracker", "app_id": "1203637303", "category": "Routine and habit building", "competitive_set": "Fabulous vs Habitica"},
    {"name": "Habitica: Gamified Taskmanager", "app_id": "994882113", "category": "Routine and habit building", "competitive_set": "Fabulous vs Habitica"},
]


def fetch_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "HabitLoopRetentionResearch/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def search_app_id(app_name):
    query = urllib.parse.urlencode(
        {
            "term": app_name,
            "country": COUNTRY,
            "media": "software",
            "limit": 1,
        }
    )
    payload = fetch_json(f"https://itunes.apple.com/search?{query}")
    results = payload.get("results", [])
    if not results:
        raise RuntimeError(f"No App Store result found for {app_name}")
    result = results[0]
    return {
        "search_name": app_name,
        "app_id": str(result["trackId"]),
        "app_name": result["trackName"],
        "seller": result.get("sellerName", ""),
        "primary_genre": result.get("primaryGenreName", ""),
        "average_rating": result.get("averageUserRating", ""),
        "rating_count": result.get("userRatingCount", ""),
    }


def lookup_app(app_config):
    if app_config.get("app_id"):
        payload = fetch_json(f"https://itunes.apple.com/lookup?id={app_config['app_id']}&country={COUNTRY}")
        results = payload.get("results", [])
        if not results:
            raise RuntimeError(f"No App Store lookup result found for {app_config['name']}")
        result = results[0]
        return {
            "search_name": app_config["name"],
            "app_id": str(result["trackId"]),
            "app_name": result["trackName"],
            "seller": result.get("sellerName", ""),
            "primary_genre": result.get("primaryGenreName", ""),
            "average_rating": result.get("averageUserRating", ""),
            "rating_count": result.get("userRatingCount", ""),
            "category": app_config.get("category", "Uncategorized"),
            "competitive_set": app_config.get("competitive_set", "Uncategorized"),
        }
    return search_app_id(app_config["name"])


def fetch_reviews(app):
    reviews = []
    for page in range(1, PAGES_PER_APP + 1):
        url = (
            f"https://itunes.apple.com/{COUNTRY}/rss/customerreviews/page={page}/"
            f"id={app['app_id']}/sortBy=mostRecent/json"
        )
        try:
            payload = fetch_json(url)
        except Exception as exc:
            print(f"Skipping page {page} for {app['app_name']}: {exc}")
            continue

        entries = payload.get("feed", {}).get("entry", [])
        if page == 1 and entries:
            entries = entries[1:]
        if not entries:
            break

        for entry in entries:
            reviews.append(
                {
                    "app_name": app["app_name"],
                    "search_name": app["search_name"],
                    "app_id": app["app_id"],
                    "seller": app["seller"],
                    "primary_genre": app["primary_genre"],
                    "app_average_rating": app["average_rating"],
                    "app_rating_count": app["rating_count"],
                    "category": app["category"],
                    "competitive_set": app["competitive_set"],
                    "review_id": entry.get("id", {}).get("label", ""),
                    "review_title": entry.get("title", {}).get("label", ""),
                    "review_text": entry.get("content", {}).get("label", ""),
                    "rating": entry.get("im:rating", {}).get("label", ""),
                    "vote_count": entry.get("im:voteCount", {}).get("label", "0"),
                    "updated": entry.get("updated", {}).get("label", ""),
                    "author": entry.get("author", {}).get("name", {}).get("label", ""),
                }
            )
        time.sleep(0.25)
    return reviews


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_reviews = []

    for app_config in APPS:
        app = lookup_app(app_config)
        print(f"Collecting {app['app_name']} ({app['app_id']})")
        app_reviews = fetch_reviews(app)
        print(f"  reviews collected: {len(app_reviews)}")
        all_reviews.extend(app_reviews)

    fieldnames = [
        "app_name",
        "search_name",
        "app_id",
        "seller",
        "primary_genre",
        "app_average_rating",
        "app_rating_count",
        "category",
        "competitive_set",
        "review_id",
        "review_title",
        "review_text",
        "rating",
        "vote_count",
        "updated",
        "author",
    ]

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_reviews)

    print(f"Wrote {len(all_reviews)} real reviews to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
