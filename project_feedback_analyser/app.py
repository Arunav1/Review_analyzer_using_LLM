import re

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

LABEL_EMOJI = {
    "positive": "😊",
    "negative": "😞",
    "neutral": "😐",
}


def post(endpoint: str, payload: dict):
    response = requests.post(f"{API_URL}{endpoint}", json=payload, timeout=120)
    if response.status_code == 429:
        raise requests.exceptions.HTTPError(
            "Gemini API quota exceeded. The free tier allows only a few requests per minute "
            "and a limited number per day. Wait and try again, or set a different GEMINI_MODEL in .env."
        )
    if not response.ok:
        # surface the API's error detail (e.g. Gemini rate limit) instead of a bare status code
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise requests.exceptions.HTTPError(f"{response.status_code}: {detail}")
    return response.json()


def analyze_review(text: str) -> dict:
    return post("/analyze", {"text": text})


def analyze_reviews(texts: list[str]) -> list[dict]:
    return post("/analyze_batch", {"texts": texts})


st.set_page_config(page_title="Feedback Analyser", page_icon="📝")
st.title("📝 Customer Feedback Analyser")
st.write("Analyze customer reviews for sentiment, score, and main theme.")

tab_single, tab_batch = st.tabs(["Single review", "Multiple reviews"])

with tab_single:
    review = st.text_area("Enter a customer review", height=150)

    if st.button("Analyze", type="primary"):
        if not review.strip():
            st.warning("Please enter a review first.")
        else:
            try:
                with st.spinner("Analyzing..."):
                    result = analyze_review(review)

                label = result["label"]
                col1, col2, col3 = st.columns(3)
                col1.metric("Sentiment", f"{LABEL_EMOJI.get(label, '')} {label.title()}")
                col2.metric("Score", f"{result['score']} / 5")
                col3.metric("Theme", result["theme"])
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the API. Is the FastAPI server running?")
            except requests.exceptions.RequestException as e:
                st.error(f"API request failed: {e}")

with tab_batch:
    st.write("Upload a .txt file or paste reviews below, one review per line.")
    uploaded_file = st.file_uploader("Upload reviews", type=["txt"])
    pasted = st.text_area("Or paste reviews here", height=150)

    if st.button("Analyze all", type="primary"):
        raw = uploaded_file.getvalue().decode("utf-8") if uploaded_file else pasted
        # drop list numbering like "1. " or "2) " at the start of each line
        reviews = [re.sub(r"^\d+[.)]\s*", "", line.strip()) for line in raw.splitlines() if line.strip()]

        if not reviews:
            st.warning("Please upload a file or paste some reviews first.")
        else:
            results = []
            try:
                with st.spinner(f"Analyzing {len(reviews)} reviews..."):
                    analyses = analyze_reviews(reviews)
                results = [{"review": text, **analysis} for text, analysis in zip(reviews, analyses)]
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the API. Is the FastAPI server running?")
            except requests.exceptions.RequestException as e:
                st.error(f"API request failed: {e}")

            if results:
                st.dataframe(results, width="stretch")

                st.subheader("Summary")
                col1, col2 = st.columns(2)
                avg_score = sum(r["score"] for r in results) / len(results)
                col1.metric("Average score", f"{avg_score:.1f} / 5")
                col2.metric("Reviews analyzed", len(results))

                label_counts = {}
                for r in results:
                    label_counts[r["label"]] = label_counts.get(r["label"], 0) + 1
                st.bar_chart(label_counts)
