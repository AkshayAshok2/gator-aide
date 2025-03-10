from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_caching import Cache
from backend.flask.lti import lti_bp
import requests
import openai
import os
import json
from dotenv import load_dotenv
import logging

# Initialize Flask app
app = Flask(__name__, static_folder='../../frontend', static_url_path='')
CORS(app)

# Logging Purposes
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1348451785966227497/3o8t4ulCGPLpRVRTL_6GL4LqfnvC-pjV_M7rSbBhrawYojH5_1muPTtTkzZtCHf67TT7"

# Function to send logs to Discord
def send_log_to_discord(message):
    data = {"content": f"🛠 Debug Log:\n{message}"}
    requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(data), headers={"Content-Type": "application/json"})

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Flask Request Logging
@app.before_request
def log_request():
    log_message = f"📢 Incoming Request: {request.method} {request.url}\nParams: {request.args.to_dict()}"
    send_log_to_discord(log_message)

@app.after_request
def log_response(response):
    if response.direct_passthrough:
        response.direct_passthrough = False  # Force Flask to load response data

    log_message = f"✅ Response: {response.status}\n{response.get_data(as_text=True)[:500]}"
    send_log_to_discord(log_message)  # Send logs to Discord
    return response

# Load environment variables
load_dotenv()

# Secret Key for session management
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_secret_key")
# Register the LTI blueprint
app.register_blueprint(lti_bp)

# Canvas API Token and LLM API Key from environment variables
CANVAS_API_TOKEN = os.getenv("CANVAS_API_TOKEN")
OPENAI_API_KEY = os.getenv("LLM_KEY")

# Configure OpenAI (LiteLLM Proxy)
client = openai.OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.ai.it.ufl.edu/v1"
)

# Canvas SmartSearch API Details
CANVAS_API_BASE_URL = "https://ufldev.instructure.com/api/v1/courses"
COURSE_ID = "180"

# Home route
@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/static/<path:path>")
def serve_static_files(path):
    return send_from_directory(app.static_folder, path)

# Chat endpoint
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"response": "Please send a valid message."}), 400

        # Step 1: Query Canvas SmartSearch API
        headers = {'Authorization': f'Bearer {CANVAS_API_TOKEN}'}
        
        smartsearch_url = f"{CANVAS_API_BASE_URL}/{COURSE_ID}/smartsearch"
        params = {"q": user_message}
        smartsearch_response = requests.get(smartsearch_url, headers=headers, params=params)
        

        if smartsearch_response.status_code != 200:
            return jsonify({"response": "Failed to fetch results from Canvas SmartSearch."}), 500
        
        smartsearch_json = smartsearch_response.json()

        # Step 2: Filter search results based on distance
        filtered_results = [
            item for item in smartsearch_json.get("results", []) if item["distance"] <= 0.55
        ]
        
        # if not filtered_results:
        #     return jsonify({"response": "No relevant information found in SmartSearch results."})

        # Step 3: Generate response using LLM (Modle can be changed via LiteLLM)
        context_data = "\n".join(
            [
                f"Title: {item.get('title', 'No Title')}\nContent: {item.get('body', 'No Content')}\n"
                for item in filtered_results
            ]
        )
        print(f"==== USER Q: {user_message} ====")
        print("==== FILTERED RESULTS FROM SMARTSEARCH ====")
        print(context_data)
        print()
        prompt = f"""
        You are a helpful educational assistant named GatorAIde designed to help students navigate their course materials in the Canvas LMS.
        If the query is a simple greeting, respond with a friendly greeting, stating who you are and what you can do in a short helpful way!
        If the query is not related to course content or outside the scope of the class, respond with a simple message, apologizing that you can not answer that question and state who you are and what you can do in a short helpful way!
        If you are answering a question, you do not have to state who you are and what you are answering. Instead be direct and straight to the point.
        A student has asked a question related to the course content. The course is Programming Fundamentals 1. Using the following context from the Canvas SmartSearch results, provide a clear, concise, and student-friendly answer:
        
        Student's Question: {user_message}
        
        Context:
        {context_data}

        Remember to keep the responses short and sweet!
        Answer the question in a way that is easy for a student to understand, and provide additional explanations if necessary.
        """

        response = client.chat.completions.create(
            model="llama-3.1-70b-instruct",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        llm_response = response.choices[0].message.content.strip()

        # Step 4: Return the generated response to the frontend
        return jsonify({"response": llm_response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the Flask server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
