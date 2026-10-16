
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from scraper import search_apps
from data_cleaning import clean_reviews
import scraper

from database import create_tables


print("SCRAPER FILE:", scraper.__file__)
st.set_page_config(
    page_title="Market Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)
create_tables()
st.title("📊 Market Intelligence & Competitor Analysis")
st.markdown("Compare competitor apps using user review data.")


st.subheader("1. Define Your Market Idea")

market_idea = st.text_input(
    "What market or app idea do you want to analyze?",
    placeholder="Example: Food delivery apps"
)

if st.button("Search Competitor Apps"):
    if not market_idea.strip():
        st.warning("Please enter a market idea first.")
    else:
        with st.spinner("Searching Google Play..."):
            try:
                results = search_apps(
                    keyword=market_idea.strip(),
                    limit=30,
                    lang="ar",
                    country="ps"
                )

                st.session_state["search_results"] = results
                st.session_state["market_idea"] = market_idea.strip()

            except Exception as e:
                st.error(f"Search failed: {e}")


if "search_results" in st.session_state:
    results = st.session_state["search_results"]

    if results:
        st.subheader("2. Select Competitor Apps")

        st.caption(
            "Market: Palestine | Select between 2 and 5 apps."
        )

        selected_apps = st.multiselect(
            "Choose competitors to analyze:",
            options=results,
            format_func=lambda item: item["title"],
            max_selections=5
        )

        if len(selected_apps) < 2:
            st.info("Please select at least 2 apps.")
        else:
            st.success(
                f"You selected {len(selected_apps)} competitor apps."
            )

            st.dataframe(
                pd.DataFrame(selected_apps),
                use_container_width=True,
                hide_index=True
            )

            if st.button("Start Competitor Analysis"):
                st.session_state["selected_apps"] = selected_apps

                if not 2 <= len(selected_apps) <= 5:
                    st.error("Please select between 2 and 5 apps.")
                else:
                    with st.spinner("Collecting competitor data..."):

                        try:
                            from scraper import collect_competitor_data
                            from analysis import run_analysis

                            with st.spinner("Collecting competitor data..."):
                                collect_competitor_data(
                                    selected_apps,
                                    review_count=200
                                )

                                clean_reviews()

                                with st.spinner("Analyzing the new competitor data..."):
                                    run_analysis()

                            st.session_state["analysis_completed"] = True
                            st.success(
                                "Competitor data collected and analyzed successfully!"
                            )

                            st.rerun()

                        except Exception as error:
                            st.error(f"Competitor analysis failed: {error}")

    else:
        st.warning(
            "No apps found. Try another market idea."
        )

if "analysis_completed" not in st.session_state:
    st.session_state["analysis_completed"] = False

DATA_DIR = "data"

review_path = os.path.join(DATA_DIR, "review_summary.csv")
rating_path = os.path.join(DATA_DIR, "rating_distribution.csv")
sentiment_path = os.path.join(DATA_DIR, "sentiment_summary.csv")

required_files = [review_path, rating_path, sentiment_path]

files_exist = all(os.path.exists(file) for file in required_files)

if files_exist and st.session_state["analysis_completed"]:
    review_df = pd.read_csv(review_path)
    rating_df = pd.read_csv(rating_path, index_col=0)
    sentiment_df = pd.read_csv(sentiment_path, index_col=0)

    ai_reviews_path = os.path.join(DATA_DIR, "competitor_reviews_ai.csv")

    if os.path.exists(ai_reviews_path):
        ai_reviews_df = pd.read_csv(ai_reviews_path)
    else:
        ai_reviews_df = pd.DataFrame()
else:
    st.info(
        "اختاري التطبيقات واضغطي Start Competitor Analysis "
        "لجمع المراجعات وإنشاء نتائج التحليل."
    )
    st.stop()

if not st.session_state["analysis_completed"]:
    st.info("Choose competitor apps and click Start Competitor Analysis to view results.")
    st.stop()

st.success("Analysis data loaded successfully.")

st.subheader("Competitor Overview")

col1, col2 = st.columns(2)

with col1:
    st.metric("Competitor Apps", len(review_df))

with col2:
    st.metric("Reviews Analyzed", int(review_df["review_count"].sum()))

st.subheader("Average Review Rating")

fig_rating = px.bar(
    review_df,
    x="title",
    y="average_rating",
    text="average_rating",
    color="title",
    title="Average Rating by Competitor",
    labels={
        "title": "Competitor",
        "average_rating": "Average Rating (out of 5)"
    }
)

fig_rating.update_yaxes(range=[0, 5])
st.plotly_chart(fig_rating, use_container_width=True)

st.subheader("Review Rating Distribution")


rating_long = rating_df.rename_axis("Competitor").reset_index()

rating_long = rating_long.melt(
    id_vars="Competitor",
    var_name="Star Rating",
    value_name="Number of Reviews"
)


fig_distribution = px.bar(
    rating_long,
    x="Star Rating",
    y="Number of Reviews",
    color="Competitor",
    barmode="group",
    title="Number of Reviews by Star Rating"
)

st.plotly_chart(fig_distribution, use_container_width=True)

st.subheader("Positive, Neutral, and Negative Reviews")


sentiment_long = sentiment_df.rename_axis("Competitor").reset_index()

sentiment_long = sentiment_long.melt(
    id_vars="Competitor",
    value_vars=["Positive %", "Neutral %", "Negative %"],
    var_name="Sentiment",
    value_name="Percentage"
)


fig_sentiment = px.bar(
    sentiment_long,
    x="Competitor",
    y="Percentage",
    color="Sentiment",
    barmode="group",
    text="Percentage",
    title="Review Sentiment Comparison",
    labels={"Percentage": "Percentage (%)"}
)

st.plotly_chart(fig_sentiment, use_container_width=True)


# ربط كل مراجعة باسم التطبيق
app_names = (
    review_df.drop_duplicates("title")
    .set_index("title")
)

id_to_name = pd.read_csv(
    os.path.join(DATA_DIR, "competitor_apps.csv")
)

id_to_name["app_id"] = id_to_name["app_id"].astype(str)
ai_reviews_df["app_id"] = ai_reviews_df["app_id"].astype(str)

app_name_map = (
    id_to_name.drop_duplicates("app_id")
    .set_index("app_id")["title"]
)

ai_reviews_df["app_name"] = ai_reviews_df["app_id"].map(app_name_map)


# أهم الاستنتاجات باللغة العربية
st.subheader("أهم الاستنتاجات 💡")

if not sentiment_df.empty:
    # التطبيق صاحب أعلى نسبة مشاعر إيجابية
    best_app = sentiment_df["Positive %"].idxmax()
    best_positive = sentiment_df.loc[best_app, "Positive %"]

    # التطبيق صاحب أعلى نسبة مشاعر سلبية
    worst_app = sentiment_df["Negative %"].idxmax()
    worst_negative = sentiment_df.loc[worst_app, "Negative %"]

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "أعلى مشاعر إيجابية",
            f"{best_positive:.1f}%"
        )
        st.write(f"**التطبيق:** {best_app}")

    with col2:
        st.metric(
            "أعلى مشاعر سلبية",
            f"{worst_negative:.1f}%"
        )
        st.write(f"**التطبيق:** {worst_app}")

    st.markdown("### 🔢 عدد المراجعات لكل تطبيق")

    for app_name, row in sentiment_df.iterrows():
        total_reviews = int(row["Total"])
        st.write(f"• **{app_name}:** {total_reviews} مراجعة")

    st.markdown("### 📊 ماذا تعني النتائج؟")

    st.write(
        f"• سجّل تطبيق **{best_app}** أعلى نسبة من "
        f"المشاعر الإيجابية، بلغت **{best_positive:.1f}%**."
    )

    st.write(
        f"• سجّل تطبيق **{worst_app}** أعلى نسبة من "
        f"المشاعر السلبية، بلغت **{worst_negative:.1f}%**. "
        "يمكن مراجعة المراجعات السلبية لمعرفة المشكلات المتكررة."
    )

    st.caption(
        "ملاحظة: الاستنتاجات مبنية على عينة المراجعات التي جُمعت، "
        "ولا تمثل بالضرورة جميع مستخدمي التطبيقات."
    )
else:
    st.info("لا توجد بيانات مشاعر كافية لاستخراج الاستنتاجات.")



st.subheader("نقاط القوة والضعف لدى المنافسين 🔎")

if not ai_reviews_df.empty:
    app_options = sorted(
        ai_reviews_df["app_name"].dropna().unique().tolist()
    )

    selected_app = st.selectbox(
        "اختاري التطبيق لتحليل مراجعاته:",
        app_options
    )

    app_reviews = ai_reviews_df[
        ai_reviews_df["app_name"] == selected_app
    ].copy()

    positive_reviews = app_reviews[
        app_reviews["ai_sentiment"] == "Positive"
    ]

    negative_reviews = app_reviews[
        app_reviews["ai_sentiment"] == "Negative"
    ]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🟢 نقاط القوة")
        st.metric("المراجعات الإيجابية", len(positive_reviews))

        if not positive_reviews.empty:
            for review in positive_reviews["review_clean"].head(5):
                st.write(f"• {review}")
        else:
            st.info("لا توجد مراجعات إيجابية في العينة.")

    with col2:
        st.markdown("### 🔴 نقاط الضعف")
        st.metric("المراجعات السلبية", len(negative_reviews))

        if not negative_reviews.empty:
            for review in negative_reviews["review_clean"].head(5):
                st.write(f"• {review}")
        else:
            st.info("لا توجد مراجعات سلبية في العينة.")
else:
    st.info("لا توجد مراجعات متاحة للتحليل.")

st.subheader("النتائج التفصيلية")
st.dataframe(review_df, use_container_width=True)

st.caption(
    "Note: Results are based on the collected review sample, "
    "not all reviews available on Google Play."
)
