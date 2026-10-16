# import os
# import pandas as pd
#
# from google_play_scraper import app as get_app
# from google_play_scraper import reviews, Sort
#
# # Paths
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DATA_DIR = os.path.join(BASE_DIR, "data")
#
# os.makedirs(DATA_DIR, exist_ok=True)
#
# APPS_PATH = os.path.join(DATA_DIR, "apps.csv")
# REVIEWS_PATH = os.path.join(DATA_DIR, "reviews.csv")
#
#
# APP_COLUMNS = [
#     "App_ID",
#     "App_Name",
#     "Rating",
#     "Ratings_Count",
#     "Installs",
#     "Category",
#     "Developer"
# ]
#
# REVIEW_COLUMNS = [
#     "التطبيق",
#     "App_ID",
#     "التقييم",
#     "التعليق",
#     "التاريخ",
#     "الإعجابات"
# ]
#
#
# def collect_data(selected_apps, review_count=100):
#     apps_data = []
#     reviews_data = []
#     errors = []
#
#     for item in selected_apps:
#         app_id = item["appId"]
#         app_title = item.get("title", app_id)
#
#         try:
#             # Fetch app information
#             info = get_app(
#                 app_id,
#                 lang="ar",
#                 country="ps"
#             )
#
#             apps_data.append({
#                 "App_ID": app_id,
#                 "App_Name": info.get("title", app_title),
#                 "Rating": info.get("score"),
#                 "Ratings_Count": info.get("ratings"),
#                 "Installs": info.get("installs"),
#                 "Category": info.get("genre"),
#                 "Developer": info.get("developer")
#             })
#
#             # Fetch recent reviews
#             result, _ = reviews(
#                 app_id,
#                 lang="ar",
#                 country="ps",
#                 sort=Sort.NEWEST,
#                 count=int(review_count)
#             )
#
#             for review in result:
#                 reviews_data.append({
#                     "التطبيق": info.get("title", app_title),
#                     "App_ID": app_id,
#                     "التقييم": review.get("score"),
#                     "التعليق": review.get("content") or "",
#                     "التاريخ": review.get("at"),
#                     "الإعجابات": review.get("thumbsUpCount", 0)
#                 })
#
#         except Exception as error:
#             errors.append(f"{app_title}: {error}")
#
#     apps_df = pd.DataFrame(apps_data, columns=APP_COLUMNS)
#     reviews_df = pd.DataFrame(reviews_data, columns=REVIEW_COLUMNS)
#
#     # Save the selected apps' latest collection
#     apps_df.to_csv(
#         APPS_PATH,
#         index=False,
#         encoding="utf-8-sig"
#     )
#
#     reviews_df.to_csv(
#         REVIEWS_PATH,
#         index=False,
#         encoding="utf-8-sig"
#     )
#
#     return apps_df, reviews_df, errors




from google_play_scraper import search, app, reviews, Sort
import pandas as pd
import os
from database import save_competitor_data

def search_apps(keyword, limit=30, lang="ar", country="ps"):
    """
    Search for Android apps on Google Play.
    """
    results = search(
        keyword,
        lang=lang,
        country=country
    )

    apps = []

    for item in results[:limit]:
        apps.append({
            "title": item.get("title"),
            "app_id": item.get("appId"),
            "url": f"https://play.google.com/store/apps/details?id={item.get('appId')}"
        })

    return apps

def get_app_details(app_id, lang="ar", country="ps"):
    """Get detailed information about an Android app."""
    details = app(
        app_id,
        lang=lang,
        country=country
    )

    return {
        "title": details.get("title"),
        "app_id": details.get("appId"),
        "rating": details.get("score"),
        "ratings_count": details.get("ratings"),
        "installs": details.get("installs"),
        "category": details.get("genre"),
        "developer": details.get("developer")
    }




def get_app_reviews(app_id, count=200, lang="ar", country="ps"):
    """Get user reviews for an Android app."""
    result, _ = reviews(
        app_id,
        lang=lang,
        country=country,
        count=count,
        sort=Sort.NEWEST
    )

    # If the requested language returns few reviews,
    # try English as a fallback.
    if len(result) < count and lang != "en":
        try:
            extra_result, _ = reviews(
                app_id,
                lang="en",
                country=country,
                count=count,
                sort=Sort.NEWEST
            )

            existing = {
                item.get("reviewId")
                for item in result
                if item.get("reviewId")
            }

            for item in extra_result:
                review_id = item.get("reviewId")

                if review_id and review_id not in existing:
                    result.append(item)
                    existing.add(review_id)

                if len(result) >= count:
                    break

        except Exception as error:
            print(f"English review fallback failed: {error}")

    review_data = []

    for review in result[:count]:
        review_data.append({
            "review_id": review.get("reviewId"),
            "app_id": app_id,
            "rating": review.get("score"),
            "review": review.get("content"),
            "date": review.get("at")
        })
    return review_data


def save_to_csv(data, filename):
    """Save data to a CSV file inside the data folder."""
    if not data:
        print(f"No data to save to {filename}.")
        return

    ensure_data_folder()
    filepath = os.path.join("data", filename)

    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"Saved {len(df)} rows to {filepath}")


def ensure_data_folder():
    """Create the data folder if it does not exist."""
    os.makedirs("data", exist_ok=True)
    print("Data folder is ready.")



def collect_competitor_data(selected_apps, review_count=200):
    """Collect details and reviews for selected competitor apps."""
    all_details = []
    all_reviews = []

    for selected in selected_apps:
        app_id = selected.get("app_id")

        if not app_id:
            print("Skipping an app without an app ID.")
            continue

        print(f"\nCollecting data for: {selected.get('title', app_id)}")

        try:
            details = get_app_details(app_id)
            all_details.append(details)

            app_reviews = get_app_reviews(
                app_id,
                count=review_count
            )

            print("TEST REVIEW:", app_reviews[0] if app_reviews else "No reviews")
            print("TEST REVIEW ID:", app_reviews[0].get("review_id") if app_reviews else None)
            all_reviews.extend(app_reviews)

            print(f"Reviews collected: {len(app_reviews)}")

        except Exception as error:
            print(f"Could not collect data for {app_id}: {error}")

    save_to_csv(all_details, "competitor_apps.csv")
    print("Review columns before saving:", list(all_reviews[0].keys()) if all_reviews else "No reviews")
    save_to_csv(all_reviews, "competitor_reviews.csv")
    save_competitor_data(all_details, all_reviews)
    print("Apps sent to database:", len(all_details))
    print("Reviews sent to database:", len(all_reviews))
    print("App names:", [item.get("title") for item in all_details])

    print("\nCompetitor data collection completed.")


if __name__ == "__main__":
    keyword = input("Enter app category (e.g., food delivery, shopping, education): ").strip()
    if not keyword:
        print("Please enter an app category.")
    else:
        apps = search_apps(keyword, limit=30, lang="ar", country="ps")

        print(f"\nSearch results for: {keyword}")
        print("-" * 50)

        for index, found_app in enumerate(apps, start=1):
            print(f"{index}. {found_app['title']}")
            print(f"   App ID: {found_app['app_id']}")
            print(f"   URL: {found_app['url']}")

        print("\nChoose 2 to 5 apps by entering their numbers separated by commas.")
        print("Example: 1,3,4")

        choice = input("Your selection: ").strip()

        try:
            numbers = [int(n.strip()) for n in choice.split(",")]

            if len(numbers) != len(set(numbers)):
                print("Please do not select the same app more than once.")
            elif not 2 <= len(numbers) <= 5:
                print("Please select between 2 and 5 apps.")
            elif any(n < 1 or n > len(apps) for n in numbers):
                print("One or more numbers are invalid.")
            else:
                selected_apps = [apps[n - 1] for n in numbers]

                print("\nSelected competitor apps:")
                for selected_app in selected_apps:
                    print(f"- {selected_app['title']} ({selected_app['app_id']})")

                print("\nStarting competitor data collection...")
                collect_competitor_data(selected_apps, review_count=200)

        except ValueError:
            print("Invalid input. Enter numbers separated by commas.")
