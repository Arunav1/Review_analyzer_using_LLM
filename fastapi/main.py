from fastapi import FastAPI
from pydantic import BaseModel
from google.genai import types
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello":"World"}

@app.get("/margin")
def margin(revenue: float, expenses: float):
    profit = revenue - expenses
    margin = (profit / revenue) * 100
    return {"profit": profit, "margin": margin}


class Review(BaseModel): #input structure to the model. 
    text: str

class sentiment(BaseModel): #output structure to the model.
    label: str
    score: int


@app.post("/sentiment")
def analyze_sentiment(review: Review):
    conversation = []
    conversation.append({
        "role":"user",
        "parts": [{"text":review}]
    })
    client = genai.Client()
    response = client.models.generate_content(
        model = "gemini-3.5-flash", 
        contents = (
            "Find the sentiment of the customer review."
            "Label must be positive, negative, or neutral."
            "score must be a number from 1(very bad) to 5(very good)"
            f"review: {review}"
        ), 
        config = types.GenerateContentConfig(
            response_mime_type = "application/json", 
            response_schema = sentiment
        )
    )
    
    conversation.append({
                "role":"model",
                "parts":[{"text": response.text}]})
    return response.parsed

    
    
    
    