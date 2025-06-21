import os
import sqlite3
from datetime import datetime

import joblib
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from googleapiclient.discovery import build
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from textblob import TextBlob
import google.generativeai as genai

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": "https://your-frontend-domain.com"}})  # Allow all origins; restrict this in production if needed

# Load environment variables for API keys
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not GENAI_API_KEY or not YOUTUBE_API_KEY:
    raise EnvironmentError("Please set GENAI_API_KEY and YOUTUBE_API_KEY environment variables.")

# Configure Gemini API
genai.configure(api_key=GENAI_API_KEY)

# Initialize YouTube API client
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Paths for pre-trained model files - assume these are uploaded with your code
MODEL_PATH = "sentiment_model.pkl"
VECTORIZER_PATH = "vectorizer.pkl"

# Load or train sentiment model and vectorizer
def load_or_train_model():
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        print("✅ Loading existing sentiment model and vectorizer...")
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
    else:
        print("⚠️ Model files not found! Training new model...")

        # Load dataset - must be included in your repo root
        dataset_path = "chatbot_data.csv"
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset file '{dataset_path}' not found!")

        df = pd.read_csv(dataset_path)

        # Calculate sentiment scores
        df["sentiment"] = df["text"].apply(lambda x: TextBlob(str(x)).sentiment.polarity if isinstance(x, str) else 0)

        # Prepare features and labels
        vectorizer = TfidfVectorizer(max_features=500)
        X = vectorizer.fit_transform(df["text"])
        y = ["positive" if score > 0 else "negative" if score < 0 else "neutral" for score in df["sentiment"]]

        model = LogisticRegression()
        model.fit(X, y)

        # Save model and vectorizer for next runs
        joblib.dump(model, MODEL_PATH)
        joblib.dump(vectorizer, VECTORIZER_PATH)

    return model, vectorizer


model, vectorizer = load_or_train_model()


# Analyze sentiment label from text
def analyze_sentiment(text):
    X = vectorizer.transform([text])
    return model.predict(X)[0]


# Fetch YouTube video based on a query
def fetch_youtube_link(query):
    try:
        search_response = youtube.search().list(
            q=query,
            part="snippet",
            maxResults=1,
            type="video"
        ).execute()

        if search_response.get("items"):
            video = search_response["items"][0]
            video_id = video["id"]["videoId"]
            video_title = video["snippet"]["title"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            return {"title": video_title, "url": video_url}
        else:
            return {"title": "No video found", "url": ""}
    except Exception as e:
        print(f"❌ YouTube API error: {e}")
        return {"title": "Error fetching video", "url": ""}


# Generate chatbot response using Gemini API
def get_gemini_response(user_message, sentiment_label):
    prompt = f"""
    You are a mental health chatbot. The user said: "{user_message}".
    The sentiment is detected as {sentiment_label}.

    Respond in a supportive and empathetic way. Keep messages short and chat-like.
    If sentiment is negative, offer words of encouragement.
    Suggest a relevant YouTube video if the user asks.
    """

    try:
        model_gemini = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = model_gemini.generate_content(prompt)

        # Pick video suggestion based on sentiment
        if sentiment_label == "negative":
            video = fetch_youtube_link("calming music for stress relief")
        elif sentiment_label == "positive":
            video = fetch_youtube_link("motivational videos for college students")
        else:
            video = fetch_youtube_link("meditation or breathing exercises")

        return {
            "message": getattr(response, "text", "I'm here for you. Stay strong! 😊"),
            "video": video
        }
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return {
            "message": "I'm here for you. Stay strong! 😊",
            "video": {"title": "Error fetching video", "url": ""}
        }


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or "message" not in data or not data["message"].strip():
            return jsonify({"error": "Message cannot be empty"}), 400

        user_message = data["message"].strip()

        sentiment_label = analyze_sentiment(user_message)
        bot_response = get_gemini_response(user_message, sentiment_label)

        return jsonify({
            "response": bot_response["message"],
            "video": bot_response["video"]
        })
    except Exception as e:
        print(f"❌ Error in /chat endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Run on port 5001 as you wanted
    app.run(host="0.0.0.0", port=5001, debug=True)
