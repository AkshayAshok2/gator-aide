from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='../../frontend', static_url_path='')
CORS(app)

# Canvas API Token and LLM API Key from environment variables
CANVAS_API_DEV_TOKEN = os.getenv("CANVAS_API_DEV_TOKEN")
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

@app.route("/<path:path>")
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
        headers = {'Authorization': f'Bearer {CANVAS_API_DEV_TOKEN}'}
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
        
        if not filtered_results:
            return jsonify({"response": "No relevant information found in SmartSearch results."})

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
        You are a helpful educational assistant designed to help students navigate their course materials.
        A student has asked a question related to the course content. Using the following context from the Canvas SmartSearch results, provide a clear, concise, and student-friendly answer:

        Context:
        {context_data}

        Student's Question: {user_message}

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
