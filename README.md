# Gator-Aide

Gator-Aide is an **LTI 1.3-compliant** AI-powered educational assistant that integrates with **Canvas LMS** to help students navigate their course materials. It leverages **Canvas SmartSearch API** and **LLMs (like Llama 3.1-70B)** to provide accurate and contextual responses to student queries.

## ☁️ Hosting Information

Our backend and frontend servers are hosted on **Render**, ensuring seamless deployment and scalability. The backend Flask API is deployed at `https://gator-aide-fubd.onrender.com`, and the frontend client is available at `https://gator-aide-client.onrender.com`.

[Visit Gator-Aide Frontend](https://gator-aide-client.onrender.com)

---

## 🚀 Features

- **LTI 1.3 Integration** with Canvas LMS
- **AI-powered responses** using OpenAI models
- **Canvas SmartSearch API** for relevant course-related answers
- **Flask API** backend with CORS support
- **Frontend Chat Interface** for user interactions

---

## 💁️ Project Structure

```
/gator-aide
│── backend/
│   │── index.py         # Main Flask backend API
│   │── lti.py           # Handles LTI 1.3 authentication and launch
│   │── requirements.txt # Backend dependencies
│── frontend/
│   │── bot.js           # Chatbot frontend logic
│   │── index.html       # Main UI file
│── README.md            # Project documentation
│── .env                 # Environment variables (API keys, secrets)
```

---

## 🛠️ Setup & Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/AkshayAshok2/gator-aide.git
cd gator-aide
```

### 2️⃣ Backend Setup

1. **Install dependencies** (Python 3.9+ required):

   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Create a `.env` file** in the backend directory and add:

   ```ini
   FLASK_SECRET_KEY=your_secret_key
   LTI_PRIVATE_KEY=your_private_key
   LTI_PUBLIC_KEY=your_public_key
   LTI_CLIENT_ID=your_client_id
   LTI_DEPLOYMENT_ID=your_deployment_id
   CANVAS_API_TOKEN=your_canvas_api_token
   LLM_KEY=your_openai_api_key
   ```

3. **Run the Flask server**:

   ```bash
   gunicorn backend.flask.index:app
   ```

   The server should start on **http://127.0.0.1:8000**.

---

### 3️⃣ Frontend Setup

1. Open `frontend/index.html` in a browser.
2. Ensure `bot.js` is correctly pointing to the backend API URL for local development:

   ```javascript
   const API_URL = "http://127.0.0.1:8000" // Backend API URL
   ```

3. The chatbot should now respond to queries using AI and Canvas SmartSearch!

---

## 🛠️ Tech Stack

- **Frontend**: JavaScript, HTML, CSS
- **Backend**: Flask, pylti1.3, OpenAI API, Canvas API
- **Deployment**: Render

