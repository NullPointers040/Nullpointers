import os
import streamlit as st
import requests
from datetime import datetime, timedelta
from groq import Groq
from bs4 import BeautifulSoup
import re
import time
import geopy.geocoders
from geopy.distance import geodesic

# Set up API keys
os.environ["GROQ_API_KEY"] = "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"  # Replace with your actual key
WEATHER_API_KEY = "7f315248aa15f08e5d5e7cc256193ffd"  # Replace with your actual key
client = Groq()

# Initialize geocoder
geolocator = geopy.geocoders.Nominatim(user_agent="streamlit_app")

# Title
st.title("AI Weekend Getaway Planner with Partner & Optional School Outreach")
st.write("Spontaneous weekend trips, personalized just for you!")

with st.sidebar:
    # Basic user inputs
    home_city = st.text_input("Enter your city of departure:")
    budget = st.number_input("Enter your budget (in INR):", min_value=5000, step=5000)
    preferences = st.text_area("Enter your preferences (e.g., adventure, relaxation, food, nightlife):")
    # New: Mood input for sentiment analysis
    mood = st.text_input("How are you feeling right now? (e.g., I’m stressed, excited, tired):")
    # Manual trip settings
    trip_length = st.number_input("Trip Duration (in days):", min_value=1, max_value=7, value=2)
    max_travel_time = st.number_input("Max Travel Time (in hours):", min_value=1, max_value=12, value=3)
    start_date = st.date_input("Select Start Date:", min_value=datetime.today().date())
    end_date = start_date + timedelta(days=trip_length)
    # Transport preference
    transport_mode = st.selectbox("Preferred Mode of Transport:",
                                  ["Any", "Car", "Bike", "Flight", "Public Transport"])
    # Web scraping toggle for educational institutions
    scrape_schools = st.checkbox("Explore local culture with student guidance (Find nearby schools/colleges within 70 km)?")

# Weather fetch function (same as before)
def get_weather(destination):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={destination}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url).json()
    if response.get("weather"):
        return response["weather"][0]["description"], response["main"]["temp"]
    return "Weather data unavailable", "-"

# Analyze sentiment and return category (same as before)
def analyze_mood(user_mood):
    sentiment_messages = [
        {"role": "system", "content": "You are an emotion analysis AI. Categorize the user's mood into one of these: 'relaxation', 'adventure', 'celebration', 'healing', or 'exploration'."},
        {"role": "user", "content": f"My current mood is: {user_mood}"}
    ]
    try:
        result = client.chat.completions.create(model="llama-3.1-8b-instant", messages=sentiment_messages)
        sentiment_category = result.choices[0].message.content.strip()
        return sentiment_category
    except Exception:
        return "relaxation"

# Function to scrape travel partners (more targeted search)
def scrape_travel_partners(budget, location="India"):
    search_query = f"travel agencies in {location} offering tours under {budget} INR"
    search_url = f"https://www.google.com/search?q={search_query}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        partner_results = []
        for link in soup.find_all('a', href=True):
            if "http" in link['href'] and "google" not in link['href']:
                if "travel" in link.text.lower() or "tours" in link.text.lower() or "agency" in link.text.lower():
                    partner_results.append(link['href'])
                elif any(keyword in link['href'].lower() for keyword in ["travel", "tour", "agency"]):
                    partner_results.append(link['href'])
        return list(set(partner_results[:5]))
    except requests.exceptions.RequestException as e:
        st.error(f"Error scraping travel partners: {e}")
        return []

# Function to extract contact information from a website (same as before)
def extract_contact_info(url):
    contact_info = {"emails": set(), "phone_numbers": set(), "contact_page": None}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text))
        phone_numbers = set(re.findall(r"(\+\d{1,3}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", text))
        contact_info["emails"].update(emails)
        contact_info["phone_numbers"].update(phone_numbers)

        # Try to find a contact us page (same logic as before)
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'contact' in href.lower() or 'reach' in href.lower():
                if href.startswith('http'):
                    contact_info["contact_page"] = href
                elif href.startswith('/'):
                    contact_info["contact_page"] = url.rstrip('/') + href
                else:
                    contact_info["contact_page"] = url.rstrip('/') + '/' + href
                break

        if not contact_info["contact_page"]:
            for path in ["/contact", "/contact-us", "/reach-us", "/about/contact"]:
                potential_url = url.rstrip('/') + path
                try:
                    contact_response = requests.get(potential_url, headers=headers, timeout=5, allow_redirects=False)
                    if contact_response.status_code == 200:
                        contact_info["contact_page"] = potential_url
                        break
                except requests.exceptions.RequestException:
                    pass

        if contact_info["contact_page"]:
            try:
                contact_response = requests.get(contact_info["contact_page"], headers=headers, timeout=10)
                contact_response.raise_for_status()
                contact_soup = BeautifulSoup(contact_response.content, 'html.parser')
                contact_text = contact_soup.get_text()
                contact_emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", contact_text))
                contact_phone_numbers = set(re.findall(r"(\+\d{1,3}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", contact_text))
                contact_info["emails"].update(contact_emails)
                contact_info["phone_numbers"].update(contact_phone_numbers)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching contact page {contact_info['contact_page']}: {e}")
            except Exception as e:
                print(f"Error processing contact page {contact_info['contact_page']}: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
    except Exception as e:
        print(f"Error extracting info from {url}: {e}")
    return contact_info

# Function to find nearby schools and colleges within a radius
def find_nearby_educational_institutions(location_name, radius_km=70):
    try:
        location = geolocator.geocode(location_name)
        if location:
            search_query = f"schools and colleges in {location_name}"
            search_url = f"https://www.google.com/search?q={search_query}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            institution_websites = set()
            for link in soup.find_all('a', href=True):
                if "http" in link['href'] and "google" not in link['href']:
                    if "school" in link.text.lower() or "college" in link.text.lower() or "vidyalaya" in link.text.lower() or "university" in link.text.lower():
                        institution_websites.add(link['href'])
                    elif any(keyword in link['href'].lower() for keyword in ["school", "college", "vidyalaya", "university"]):
                        institution_websites.add(link['href'])

            nearby_institutions = []
            for website in list(institution_websites)[:10]:  # Limit to first 10 for geocoding
                try:
                    website_content = requests.get(website, headers=headers, timeout=5)
                    website_soup = BeautifulSoup(website_content.content, 'html.parser')
                    address_element = website_soup.find("address")
                    if address_element:
                        address = address_element.get_text(separator=", ", strip=True)
                        institution_location = geolocator.geocode(address)
                        if institution_location and location:
                            distance = geodesic((location.latitude, location.longitude),
                                                (institution_location.latitude, institution_location.longitude)).km
                            if distance <= radius_km:
                                nearby_institutions.append((website, address))
                except Exception as e:
                    print(f"Error geocoding or fetching from {website}: {e}")
            return nearby_institutions
        else:
            st.error(f"Could not geocode your home city: {home_city}")
            return []
    except Exception as e:
        st.error(f"Error finding nearby educational institutions: {e}")
        return []

# Generate trip on button click
if st.button("Plan My Getaway!"):
    if not home_city or not budget or not preferences or not mood:
        st.error("Please fill in all fields to generate your itinerary.")
    else:
        with st.spinner("Analyzing your mood and planning your escape..."):
            # Get sentiment from mood
            sentiment_category = analyze_mood(mood)
            trip_plan = ""
            destination = "Unknown"
            try:
                messages = [
                    {"role": "system", "content": "You are an AI travel planner specializing in emotionally intelligent weekend getaways."},
                    {"role": "user", "content": (
                        f"I am in {home_city} with a budget of ₹{budget}. I want a getaway from {start_date.strftime('%Y-%m-%d')} "
                        f"to {end_date.strftime('%Y-%m-%d')}. My preferences: {preferences}. My current mood is: '{mood}', "
                        f"so I need a trip focused on '{sentiment_category}'. Max travel time: {max_travel_time} hours. "
                        f"My preferred mode of transportation is {transport_mode}. "
                        "Recommend a great destination with an itinerary including transport, activities, food, and accommodation."
                    )}
                ]
                response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=messages)
                trip_plan = response.choices[0].message.content
                # Extract destination for weather
                if "Destination:" in trip_plan:
                    destination = trip_plan.split("Destination:")[1].split("\n")[0].strip()
                weather, temp = get_weather(destination)
                st.success("Here's your perfect weekend getaway! 🎉")
                st.subheader(f" Destination: {destination}")
                st.write(f"Weather: {weather}, {temp}°C")
                st.subheader("Your Itinerary:")
                st.markdown(trip_plan, unsafe_allow_html=True)

                st.subheader("Potential Travel Partners:")
                travel_partner_websites = scrape_travel_partners(budget, destination)
                if travel_partner_websites:
                    for website in travel_partner_websites:
                        st.write(f"Website: {website}")
                        with st.spinner(f"Fetching contact info from {website}..."):
                            contact_info = extract_contact_info(website)
                            if contact_info["emails"]:
                                st.write(f"  Potential contact emails: {', '.join(list(contact_info['emails'])[:2])} (Limited to 2)")
                            else:
                                st.write("  Could not find direct emails on this website.")
                            if contact_info["contact_page"]:
                                st.write(f"  Found a contact page: {contact_info['contact_page']}")
                            if contact_info["phone_numbers"]:
                                st.write(f"  Potential phone numbers: {', '.join(list(contact_info['phone_numbers'])[:2])} (Limited to 2)")
                        time.sleep(2)
                else:
                    st.info("No travel partners found based on the current scraping logic.")

                if scrape_schools and destination != "Unknown":
                    st.subheader(f"Nearby Schools & Colleges (within 70 km of {destination}) for Cultural Exploration:")
                    nearby_institutions = find_nearby_educational_institutions(destination, radius_km=70)
                    if nearby_institutions:
                        for website, address in nearby_institutions:
                            st.write(f"Website: {website}")
                            st.write(f"Approximate Address: {address}")
                            st.info(f"  To find the Headmaster/Principal's email, visit the website and look for 'Contact Us', 'Administration', or 'Staff Directory'.")
                        time.sleep(2)
                    else:
                        st.info(f"No nearby educational institutions found within 70 km of {destination} based on the current logic.")
                elif scrape_schools:
                    st.info("Destination is unknown, cannot find nearby schools/colleges.")

            except Exception as e:
                st.error(f"Oops! Something went wrong: {e}")