# 🌍✨ HIDDEN HORIZONS

**HIDDEN HORIZONS** is a personalized AI-powered weekend getaway planner built with Streamlit. It recommends destinations, travel itineraries, accommodations, and transport options based on your **mood**, **budget**, **preferences**, and **trip duration**. Whether you're an adventurer, a seeker of relaxation, or even an architecture student looking for educational escapes — this app tailors your trip uniquely for you.

---

## 🚀 Features

- 🔐 **User Authentication:** Sign up and log in to save your planning session.
- 💬 **Mood Analyzer:** AI categorizes your emotional state to suggest mood-aligned destinations.
- 📍 **Destination Predictor:** Dynamically selects ideal travel spots based on input.
- ☀️ **Live Weather Forecasts:** Integrates OpenWeather API for real-time updates.
- 🏨 **Accommodation Recommender:** Suggests budget-optimized stay options.
- 🚆 **Transport Optimizer:** Picks cheap and fast routes (train, bus, etc.).
- 🎓 **Student-Specific Recommendations:** If you're an architecture student, get culturally rich destinations with nearby architecture schools.
- ✍️ **Contact Form:** A simple contact page for feedback or queries.
- 📱 **Mobile-Friendly UI:** Responsive design with custom CSS styling.

---

## 🧰 Tech Stack

| Technology         | Description                                           |
|--------------------|-------------------------------------------------------|
| **Streamlit**      | Frontend and backend interface                        |
| **Python**         | Core programming language                             |
| **SQLite**         | User authentication & session persistence             |
| **Groq (LLaMA 3.1)** | AI chat model for mood analysis and planning         |
| **Google Gemini**  | Generative AI API for planning suggestions            |
| **OpenWeather API**| Real-time weather forecasts                           |
| **BeautifulSoup (optional)** | For future scraping implementations         |
| **Custom CSS**     | Enhanced visuals and responsive UI                    |

---

## 🔧 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/hidden-horizons.git
   cd hidden-horizons

2.  ```bash
   python -m venv venv
source venv/bin/activate    # For macOS/Linux
venv\Scripts\activate       # For Windows

4.  ```bash
    pip install -r requirements.txt

5.  ```bash
    GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_google_gemini_api_key
WEATHER_API_KEY=your_openweather_api_key

6.  ```bash
    streamlit run app.py

Built by NullPointers team.
Designed for personalized and intelligent travel planning.
