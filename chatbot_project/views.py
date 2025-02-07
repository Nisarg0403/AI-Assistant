import spacy
import json
import subprocess

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .knowledge_base import knowledge  # Import the knowledge base
from .app_commands import app_commands
import requests

# Load spaCy model
nlp = spacy.load("en_core_web_lg")

# WeatherStack API URL and API Key (replace YOUR_API_KEY with your actual key)
API_KEY = '1511a6ddd736b1669dba33a6ff806b43'  # Add your WeatherStack API key here
BASE_URL = 'http://api.weatherstack.com/current'


# Home Page (Chatbot UI)
def chatbot_view(request):
    return render(request, "chatbot/chat.html")  # Renders the chat.html template


@login_required
def chatbot_home(request):
    return render(request, "chatbot/chat.html")


# Chatbot Response Logic
@csrf_exempt
def get_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')

            # Simple Chatbot Logic (Weather, Knowledge-Based Questions, and App Launching)
            if "weather" in user_message.lower():
                # Extract city name from the user message
                city = user_message.lower().replace("weather", "").strip()

                if city:
                    # Fetch weather info for the city
                    weather_response = get_weather(city)
                    return JsonResponse({'response': weather_response})
                else:
                    return JsonResponse({'response': "Please provide a city name to check the weather."})
            elif "open" in user_message.lower() or "launch" in user_message.lower():
                # Extract application name from the user message
                app_name = user_message.lower().replace("open", "").replace("launch", "").strip()

                # Launch the application
                launch_response = launch_app(app_name)
                return JsonResponse({'response': launch_response})
            else:
                # Use spaCy to find the best match for knowledge-based questions
                bot_response = get_knowledge_answer(user_message)
                return JsonResponse({'response': bot_response})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


# Function to retrieve knowledge-based responses
def get_knowledge_answer(user_message):
    # Process the user's message with spaCy
    user_doc = nlp(user_message.lower())

    # Find the best match from the knowledge base
    best_match = None
    best_similarity = 0.0

    for question, answer in knowledge.items():
        question_doc = nlp(question.lower())
        similarity = user_doc.similarity(question_doc)

        if similarity > best_similarity:
            best_similarity = similarity
            best_match = answer

    # If no match is found, return a default message
    if best_similarity > 0.5:  # Threshold for similarity (can be adjusted)
        return best_match
    else:
        return "Sorry, I didn't understand that. Can you rephrase?"


# Function to fetch weather information using WeatherStack API
def get_weather(city):
    try:
        # Make an API call to WeatherStack to get the weather data
        response = requests.get(f"{BASE_URL}?access_key={API_KEY}&query={city}")
        data = response.json()

        if 'current' in data:
            # Extracting relevant data from the API response
            weather = data['current']['weather_descriptions'][0]
            temp = data['current']['temperature']
            city_name = data['location']['name']
            country = data['location']['country']

            return f"The current weather in {city_name}, {country} is {weather} with a temperature of {temp}°C."
        else:
            return "Sorry, I couldn't fetch the weather information. Please check the city name or try again later."
    except requests.RequestException as e:
        return f"An error occurred: {e}"


# Function to launch an application
def launch_app(app_name):
    try:
        app_name = app_name.lower()
        for key in app_commands:
            if key in app_name:
                subprocess.Popen([app_commands[key]])
                return f"Opening {key.capitalize()}."
        return "Sorry, I can't open that application."
    except Exception as e:
        return f"An error occurred while trying to open {app_name}: {e}"



