import os
import time

from google import genai
from google.genai import types, errors
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv()

app = FastAPI()

# each Gemini model has its own free-tier quota, so this can be switched from .env when one runs out
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

INSTRUCTIONS = (
    "label must be 'positive', 'negative', or 'neutral'."
    "score must be a number between 1(very bad) and 5(very good)."
    "theme must be a single lower case word for the main topic, for example (delivery, price, taste, quality, service)."
)

class Review(BaseModel):
    text: str

class Reviews(BaseModel):
    texts: list[str]

class Analysis(BaseModel):
    label: str
    score: int
    theme: str


def generate(contents, schema, retries = 3):
    client = genai.Client()
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model = MODEL,
                contents = contents,
                config = types.GenerateContentConfig(
                    response_mime_type = "application/json",
                    response_schema = schema
                ),
            )
            break
        except errors.ServerError as e:
            # 5xx errors like "model overloaded" are usually temporary, so wait and try again
            if attempt == retries - 1:
                raise HTTPException(status_code=e.code, detail=e.message)
            time.sleep(2 ** (attempt + 1))
        except errors.APIError as e:
            # pass Gemini's real status (e.g. 429 rate limit) to the client instead of a generic 500
            raise HTTPException(status_code=e.code, detail=e.message)

    if response.parsed is None:
        raise HTTPException(status_code=502, detail="Gemini returned an invalid response.")
    return response.parsed


@app.post("/analyze")
def analyze(review: Review):
    return generate(
        "Analyze the customer review."
        f"{INSTRUCTIONS}"
        f"Review: {review.text}",
        Analysis
    )


@app.post("/analyze_batch")
def analyze_batch(reviews: Reviews):
    # one Gemini call for all reviews, so a large file doesn't hit the requests-per-minute limit
    numbered = "\n".join(f"{i + 1}. {text}" for i, text in enumerate(reviews.texts))
    results = generate(
        f"Analyze each of the following {len(reviews.texts)} customer reviews."
        "Return exactly one analysis per review, in the same order."
        f"{INSTRUCTIONS}"
        f"Reviews:\n{numbered}",
        list[Analysis]
    )

    if len(results) != len(reviews.texts):
        raise HTTPException(
            status_code=502,
            detail=f"Expected {len(reviews.texts)} analyses but got {len(results)}."
        )
    return results
