import spacy
import json
import subprocess
import requests
import logging
import time
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from admin_panel.models import FAQ, QueryLog
from .app_commands import app_commands
from django.contrib.sessions.models import Session
from django.core.paginator import Paginator

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load spaCy NLP model
try:
    nlp = spacy.load("en_core_web_lg")
    logger.info("SpaCy model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load SpaCy model: {e}")
    nlp = None

# WeatherStack API credentials
API_KEY = '1511a6ddd736b1669dba33a6ff806b43'
BASE_URL = 'http://api.weatherstack.com/current'

# Contact details for escalation prompt
CONTACT_PHONE = "+1 (234) 567-890"
CONTACT_EMAIL = "support@conversa.com"


def check_authentication(request):
    if request.user.is_authenticated:
        return JsonResponse({"is_authenticated": True})
    return JsonResponse({"is_authenticated": False})


def homepage(request):
    faqs = FAQ.objects.all()[:4]  # Limit to 4 FAQs
    return render(request, 'chatbot/homepage.html', {'faqs': faqs})


class KnowledgeBase:
    def get_answer(self, user_message):
        user_message_clean = user_message.lower().strip()
        logger.debug(f"Processing query: {user_message_clean}")

        # Handle simple greetings explicitly
        greetings = ["hi", "hello", "hey", "hola"]
        if user_message_clean in greetings:
            return "Hello! How can I assist you today?", None

        # Split user query into words
        user_words = set(user_message_clean.split())
        if not user_words:
            return "Sorry, I didn't understand that. Could you please provide more details?", None

        # Define key content words
        key_words = {"payment", "account"}
        generic_words = {"issues", "queries"}

        best_match_score, best_match, matched_faq = 0, None, None

        # Compare with all FAQs
        for faq in FAQ.objects.all():
            faq_question = faq.question.lower()
            faq_words = set(faq_question.split())
            # Count matching words with weights
            common_words = user_words.intersection(faq_words)
            match_score = 0
            for word in common_words:
                if word in key_words:
                    match_score += 3
                elif word in generic_words:
                    match_score += 1
                else:
                    match_score += 2

            logger.debug(
                f"Comparing '{user_message_clean}' with FAQ '{faq.question}': Matching words = {common_words}, Score = {match_score}")

            if match_score > best_match_score:
                best_match_score = match_score
                best_match = faq.answer
                matched_faq = faq
            elif match_score == best_match_score and match_score > 0:
                current_ratio = match_score / len(faq_words)
                best_ratio = best_match_score / len(set(matched_faq.question.lower().split()))
                if current_ratio > best_ratio:
                    best_match = faq.answer
                    matched_faq = faq

        # Lower the minimum score threshold for better matching
        min_score = 1
        if best_match_score >= min_score:
            logger.info(f"Matched FAQ: '{matched_faq.question}' with score {best_match_score}")
            if matched_faq.children.exists():
                sub_faqs = matched_faq.children.all()
                sub_faq_data = [{"question": sub_faq.question} for sub_faq in sub_faqs]
                return {"sub_faqs": sub_faq_data}, matched_faq
            elif matched_faq.answer:
                return matched_faq.answer, matched_faq
            else:
                return "I found a match, but there’s no detailed answer available. Can you specify what you need?", matched_faq

        logger.info(
            f"No match found for '{user_message_clean}' with sufficient score (required: {min_score}, got: {best_match_score})")
        return "Sorry, I didn't understand that. Could you please provide more details?", None


class WeatherService:
    def get_weather(self, city):
        if not city:
            return "Please provide a city name to check the weather."

        try:
            response = requests.get(f"{BASE_URL}?access_key={API_KEY}&query={city}")
            data = response.json()

            if 'current' in data:
                weather = data['current']['weather_descriptions'][0]
                temp = data['current']['temperature']
                city_name = data['location']['name']
                country = data['location']['country']
                return f"The current weather in {city_name}, {country} is {weather} with a temperature of {temp}°C."
            else:
                return "Sorry, I couldn't fetch the weather information for that location."

        except requests.RequestException as e:
            logger.error(f"Weather API error: {e}")
            return f"An error occurred: {e}"


class AppLauncher:
    def launch(self, app_name):
        try:
            app_name = app_name.lower()
            for key in app_commands:
                if key in app_name:
                    subprocess.Popen([app_commands[key]])
                    return f"Opening {key.capitalize()}."
            return "Sorry, I can't open that application."
        except Exception as e:
            logger.error(f"App launch error: {e}")
            return f"An error occurred: {e}"


class Chatbot:
    def __init__(self):
        self.knowledge_base = KnowledgeBase()
        self.weather_service = WeatherService()
        self.app_launcher = AppLauncher()

    def get_response(self, user_message, session):
        # Check session context
        context = session.get('chat_context', {})
        logger.debug(f"Current context: {context}")

        if "weather" in user_message.lower():
            city = user_message.lower().replace("weather", "").strip()
            if not city:
                # Set context to expect a city name
                session['chat_context'] = {'intent': 'weather', 'awaiting': 'city'}
                session.modified = True
                return self.weather_service.get_weather(city), None
            return self.weather_service.get_weather(city), None
        elif context.get('intent') == 'weather' and context.get('awaiting') == 'city':
            # User provided a city name after "weather" prompt
            city = user_message.strip()
            session['chat_context'] = {}  # Clear context after use
            session.modified = True
            return self.weather_service.get_weather(city), None
        elif "open" in user_message.lower() or "launch" in user_message.lower():
            app_name = user_message.lower().replace("open", "").replace("launch", "").strip()
            return self.app_launcher.launch(app_name), None
        else:
            return self.knowledge_base.get_answer(user_message)


chatbot_instance = Chatbot()


def chatbot_view(request):
    welcome_message = "Hello! How can I assist you today?"
    faqs = FAQ.objects.all()[:4]
    return render(request, "chatbot/chat.html", {
        "welcome_message": welcome_message,
        "faqs": faqs
    })


@login_required
def chatbot_home(request):
    welcome_message = "Hello! How can I assist you today?"
    faqs = FAQ.objects.all()[:4]
    return render(request, "chatbot/chat.html", {
        "welcome_message": welcome_message,
        "faqs": faqs
    })


@csrf_exempt
def get_response(request):
    if request.method == "POST":
        try:
            start_time = time.time()
            data = json.loads(request.body)
            user_message = data.get('message', '')
            if not user_message:
                logger.error("No message provided in request")
                return JsonResponse({'error': 'No message provided'}, status=400)

            logger.debug(f"Received user message: {user_message}")
            # Ensure session is initialized
            if not request.session.session_key:
                request.session.create()

            bot_response, matched_faq = chatbot_instance.get_response(user_message, request.session)

            # Session-based query tracking
            session_key = request.session.session_key

            # Get recent queries for this session (last 5 minutes)
            recent_queries = QueryLog.objects.filter(
                timestamp__gte=timezone.now() - timezone.timedelta(minutes=5),
                session_key=session_key
            ).order_by('-timestamp')

            # Detect frustration signals
            frustration_signals = ["not helpful", "useless", "didn't work", "still confused"]
            is_frustrated = any(signal in user_message.lower() for signal in frustration_signals)
            repeat_count = sum(
                1 for q in recent_queries if q.query_text.lower().strip() == user_message.lower().strip())
            unresolved_count = recent_queries.filter(unresolved=True).count()

            # Only escalate after stricter conditions
            escalate = False
            if (is_frustrated and unresolved_count >= 2) or repeat_count >= 3 or unresolved_count >= 4:
                escalate = True
                logger.info(
                    f"Escalation triggered: Frustrated={is_frustrated}, Repeats={repeat_count}, Unresolved={unresolved_count}")

            # Handle structured sub-FAQ responses
            response_data = {}
            if isinstance(bot_response, dict) and 'sub_faqs' in bot_response:
                response_data['sub_faqs'] = bot_response['sub_faqs']
            else:
                bot_response = bot_response or "Sorry, I couldn't process your request."
                response_data['response'] = bot_response

            # Add escalation prompt only if triggered
            if escalate:
                response_data['escalate'] = True
                response_data['contact'] = {
                    'phone': CONTACT_PHONE,
                    'email': CONTACT_EMAIL,
                    'message': "It seems I couldn’t fully assist you. Would you like to contact support?"
                }

            lead_keywords = ["how does this work", "tell me more", "what can you do", "interested", "details"]
            is_lead = any(keyword in user_message.lower() for keyword in lead_keywords)

            # Calculate response time
            response_time = time.time() - start_time

            # Log the query with session key
            try:
                QueryLog.objects.create(
                    query_text=user_message,
                    timestamp=timezone.now(),
                    matched_faq=matched_faq,
                    unresolved=matched_faq is None,
                    response_time=response_time,
                    is_lead=is_lead,
                    session_key=session_key
                )
                logger.debug("Query logged successfully with response time: %s seconds, is_lead: %s", response_time,
                             is_lead)
            except Exception as e:
                logger.error(f"Failed to log query: {e}")

            return JsonResponse(response_data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in get_response: {e}")
            return JsonResponse({'error': 'Sorry, there was an error processing your request.'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def get_sub_faqs(request, faq_id):
    sub_faqs = FAQ.objects.filter(parent_id=faq_id)
    data = {
        'sub_faqs': [
            {
                'id': faq.id,
                'question': faq.question,
                'hasChildren': faq.children.exists(),
                'answer': faq.answer or ''
            } for faq in sub_faqs
        ]
    }
    return JsonResponse(data)


def get_faqs(request):
    page = int(request.GET.get('page', 0)) + 1  # Convert to 1-based indexing for Paginator
    limit = int(request.GET.get('limit', 5))

    faqs = FAQ.objects.all().order_by('id')
    paginator = Paginator(faqs, limit)
    total_faqs = paginator.count

    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)  # Fallback to first page if out of range

    faq_list = [
        {
            'id': faq.id,
            'question': faq.question,
            'hasChildren': faq.children.exists(),
            'answer': faq.answer or ''
        } for faq in page_obj
    ]

    return JsonResponse({
        'faqs': faq_list,
        'total_faqs': total_faqs
    })