from flask import Flask, request, jsonify, send_from_directory, Blueprint, redirect, session
from flask_cors import CORS
from flask_caching import Cache
# from backend.flask.lti import lti_bp
import requests
import openai
import os
import json
from dotenv import load_dotenv
import logging

# Temporary
from pylti1p3.tool_config import ToolConfDict
from pylti1p3.exception import LtiException
from pylti1p3.contrib.flask import (
    FlaskRequest, 
    FlaskOIDCLogin, 
    FlaskMessageLaunch, 
    FlaskSessionService, 
    FlaskCookieService,
    FlaskCacheDataStorage
)

# =============================================
# Initialize Flask app
# =============================================
app = Flask(__name__, static_folder='../../frontend', static_url_path='')
CORS(app)
# Configure Flask caching
app.config["CACHE_TYPE"] = "simple"
cache = Cache(app)
cache.init_app(app) 

# =============================================
# ============== WEBHOOK LOGGING ==============
# =============================================
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

# # Register the LTI blueprint
# app.register_blueprint(lti_bp)


# =============================================
# =========== Chatbot Functionality ===========
# =============================================

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
    
# =============================================
# =========== LTI 1.3 Functionality ===========
# =============================================

# Set up config
private_key_pem = os.environ.get("LTI_PRIVATE_KEY", "")
public_key_pem = os.environ.get("LTI_PUBLIC_KEY", "")
if not private_key_pem or not public_key_pem:
    raise RuntimeError("Missing LTI_PRIVATE_KEY or LTI_PUBLIC_KEY in environment!")
 
issuer = "https://canvas.instructure.com"
client_id = os.environ.get("LTI_CLIENT_ID")
deployment_id = os.environ.get("LTI_DEPLOYMENT_ID", "")

pylti_config_dict = {
    issuer: [
        {
            "default": True,
            "client_id": client_id,
            "auth_login_url": "https://sso.canvaslms.com/api/lti/authorize_redirect",
            "auth_token_url": "https://sso.canvaslms.com/login/oauth2/token",
            "key_set_url": "https://sso.canvaslms.com/api/lti/security/jwks",
            "deployment_ids": [deployment_id]
        }
    ]
}

tool_conf = ToolConfDict(pylti_config_dict)
tool_conf.set_private_key(issuer, private_key_pem, client_id=client_id)
tool_conf.set_public_key(issuer, public_key_pem, client_id=client_id)

class ExtendedFlaskMessageLaunch(FlaskMessageLaunch):

    def validate_nonce(self):
        """
        Probably it is bug on "https://lti-ri.imsglobal.org":
        site passes invalid "nonce" value during deep links launch.
        Because of this in case of iss == http://imsglobal.org just skip nonce validation.

        """
        iss = self.get_iss()
        deep_link_launch = self.is_deep_link_launch()
        if iss == "http://imsglobal.org" and deep_link_launch:
            return self
        return super().validate_nonce()


def get_launch_data_storage():
    return FlaskCacheDataStorage(cache)

# JWKS ENDPOINT
@app.route("/lti/jwks", methods=["GET"])
def lti_jwks():
    try:
        # Fetch the public JWKS from tool_conf.
        jwks = tool_conf.get_jwks(issuer, client_id)
        return jsonify(jwks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# LOGIN INITIATION (OIDC)
@app.route("/lti/login_initiation", methods=["GET", "POST"])
def lti_login_initiation():
    try:
        flask_request = FlaskRequest()
        launch_data_storage = get_launch_data_storage()

        oidc_login = FlaskOIDCLogin(flask_request, tool_conf, launch_data_storage=launch_data_storage)
        return oidc_login.enable_check_cookies().redirect()

    except LtiException as e:
        logging.error(f"LTI error: {str(e)}")
        return jsonify({"error": f"LTI error: {str(e)}"}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": str(e)}), 400

# LTI LAUNCH
@app.route("/lti/launch", methods=["GET", "POST"])
def lti_launch():
    try:
        # Use FlaskRequest, launch data storage, and ExtendedFlaskMessageLaunch
        flask_request = FlaskRequest()
        launch_data_storage = get_launch_data_storage()
        message_launch = ExtendedFlaskMessageLaunch(flask_request, tool_conf, launch_data_storage=launch_data_storage)
        message_launch_data = message_launch.get_launch_data()

        # Debugging output (prints launch data for verification)
        logging.debug(json.dumps(message_launch_data, indent=4))


        # Store the launch data in session
        session["lti_launch_data"] = message_launch_data

        # Redirect to main UI (unchanged from original implementation)
        return redirect("https://gator-aide-fubd.onrender.com")

    except LtiException as e:
        return jsonify({"error": f"LTI error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Run the Flask server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
