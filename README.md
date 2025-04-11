# Nullpointers
ADVAYA-2025
# 🧠 AI Weekend Getaway Planner

Spontaneous weekend trips, personalized just for you — with optional cultural immersion!

## ✨ Features

- 🤖 **AI-based Getaway Planning**: Suggests destinations, activities, food, and accommodation based on your **mood**, preferences, and budget.
- ☀️ **Live Weather Info**: Fetches real-time weather data for your destination.
- 🧳 **Travel Partners Scraping**: Finds websites of travel agencies that fit your budget and destination.
- 📬 **Contact Info Extractor**: Extracts phone numbers, emails, and contact pages from travel partner websites.
- 🏫 **Cultural Immersion**: Optionally suggests nearby **schools/colleges** within a 70 km radius of your destination for outreach/cultural exchange.

## 🛠️ How It Works

1. **User Input**:
   - Users enter their home city, budget, preferences, mood, trip duration, and transportation preferences through the sidebar.

2. **Mood Analysis**:
   - The app uses LLaMA-3.1-8B Instant (via Groq API) to analyze the mood and map it to a travel theme like _relaxation_, _adventure_, _exploration_, etc.

3. **AI Trip Planning**:
   - Based on inputs and mood theme, the AI generates a full itinerary including destination, activities, accommodation, and local experiences.

4. **Weather Forecast**:
   - The app fetches real-time weather data for the suggested destination using OpenWeatherMap API.

5. **Travel Partner Scraping**:
   - Scrapes Google search results to find travel agencies under the given budget.
   - Extracts emails, phone numbers, and contact pages from their websites.

6. **School & College Finder **:
   - The app geocodes the destination and finds educational institutions within a 70 km radius.
   - Scrapes and filters nearby school/college websites with geolocation matching.


## 🧩 Tech Stack

- **Frontend**: Streamlit
- **AI & NLP**: Groq LLaMA-3.1-8B-Instant
- **APIs**:
  - OpenWeatherMap (for weather)
  - Groq (for sentiment + itinerary)
- **Web Scraping**: BeautifulSoup, `requests`, `re`
- **Geolocation**: Geopy
- **Python Libraries**: datetime, time, os, re


## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ai-weekend-getaway-planner.git
cd ai-weekend-getaway-planner
```

### 2. Set Up Virtual Environment (Optional but Recommended)

```bash
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

<details>
<summary>📦 Sample <code>requirements.txt</code> (if not already created)</summary>

```txt
streamlit
requests
beautifulsoup4
geopy
groq
```

</details>

### 4. Set Environment Variables

Create a `.env` file or set environment variables manually:

```bash
export GROQ_API_KEY=your_groq_api_key
export WEATHER_API_KEY=your_openweather_api_key
```

Or on Windows CMD:

```cmd
set GROQ_API_KEY=your_groq_api_key
set WEATHER_API_KEY=your_openweather_api_key
```

### 5. Run the Streamlit App

```bash
streamlit run app.py
```

> Replace `app.py` with the name of your Python file if it differs.

## 📌 Notes

- Uses **Groq API (LLaMA 3.1)** for emotion detection and trip planning.
- Uses **OpenWeatherMap API** for weather info.
- Web scraping logic may need updates depending on changes in Google search structures.
- Make sure you have an active internet connection for geocoding, API calls, and scraping.

## 📎 Optional

### ZIP Package
If you received this as a `.zip` file:
1. Extract it.
2. Navigate into the folder.
3. Continue from step 2 above.

---

## 📮 Feedback or Contributions?

Feel free to submit issues or PRs if you'd like to contribute!
