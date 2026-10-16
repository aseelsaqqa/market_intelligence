
import sqlite3
import os

DB_PATH = os.path.join("data", "market_intelligence.db")


def get_connection():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH)

def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS competitors (
            app_id TEXT PRIMARY KEY,
            title TEXT,
            developer TEXT,
            rating REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id TEXT PRIMARY KEY,
            app_id TEXT NOT NULL,
            review_text TEXT,
            rating INTEGER,
            review_date TEXT,
            sentiment TEXT,
            FOREIGN KEY (app_id) REFERENCES competitors(app_id)
        )
    """)

    connection.commit()
    connection.close()

    print("Database tables created successfully!")

def check_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """)

    tables = cursor.fetchall()
    print("Tables in database:")

    for table in tables:
        print(table[0])

    connection.close()



def save_competitor_data(apps, reviews):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM reviews")
    cursor.execute("DELETE FROM competitors")

    for app in apps:
        cursor.execute("""
            INSERT OR REPLACE INTO competitors
            (app_id, title, developer, rating)
            VALUES (?, ?, ?, ?)
        """, (
            str(app.get("app_id", "")),
            app.get("title"),
            app.get("developer"),
            app.get("rating")
        ))

    for index, review in enumerate(reviews):
        app_id = str(review.get("app_id", ""))
        review_text = review.get("review", "")
        rating = review.get("rating")
        review_date = str(review.get("date", ""))

        review_id = str(review.get("review_id") or f"{app_id}_{index}")

        cursor.execute("""
            INSERT OR REPLACE INTO reviews
            (review_id, app_id, review_text, rating, review_date, sentiment)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            review_id,
            app_id,
            review_text,
            rating,
            review_date,
            None
        ))

    connection.commit()
    connection.close()

    print("Competitor data saved to SQLite successfully!")


def check_saved_data():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM competitors")
    print("Competitors stored:", cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM reviews")
    print("Reviews stored:", cursor.fetchone()[0])

    cursor.execute("""
                   SELECT COUNT(*)
                   FROM reviews
                   WHERE sentiment IS NOT NULL
                   """)
    print("Reviews with saved sentiment:", cursor.fetchone()[0])

    cursor.execute("""
        SELECT app_id, title
        FROM competitors
        WHERE app_id = 'test_app'
    """)
    print("Test app:", cursor.fetchone())

    cursor.execute("""
        SELECT app_id, review_text, rating
        FROM reviews
        WHERE app_id = 'test_app'
    """)
    print("Test review:", cursor.fetchone())

    connection.close()

def remove_test_data():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM reviews WHERE app_id = ?",
        ("test_app",)
    )

    cursor.execute(
        "DELETE FROM competitors WHERE app_id = ?",
        ("test_app",)
    )

    connection.commit()
    connection.close()

    print("Test data removed successfully!")

def show_reviews_per_app():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT c.title, c.app_id, COUNT(r.review_id)
        FROM competitors c
        LEFT JOIN reviews r ON c.app_id = r.app_id
        GROUP BY c.app_id, c.title
        ORDER BY c.title
    """)

    print("\nReviews per app:")
    for row in cursor.fetchall():
        print(f"{row[0]} | {row[1]} | Reviews: {row[2]}")

    connection.close()

def clear_previous_analysis():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM reviews")
    cursor.execute("DELETE FROM competitors")

    connection.commit()
    connection.close()

    print("Previous analysis data cleared successfully!")



def update_review_sentiments(reviews):
    connection = get_connection()
    cursor = connection.cursor()

    updated_count = 0

    for review in reviews:
        review_id = review.get("review_id")
        app_id = str(review.get("app_id", ""))
        sentiment = review.get("ai_sentiment")

        if not review_id or not sentiment:
            continue

        cursor.execute("""
            UPDATE reviews
            SET sentiment = ?
            WHERE review_id = ? AND app_id = ?
        """, (sentiment, str(review_id), app_id))

        updated_count += cursor.rowcount

    connection.commit()
    connection.close()

    print("Review sentiments updated:", updated_count)



if __name__ == "__main__":
    create_tables()
    check_saved_data()
    show_reviews_per_app()