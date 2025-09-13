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
CONTACT_EMAIL = "contact@conversa.com"


def check_authentication(request):
    logger.debug(f"Checking authentication for user: {request.user}")
    if request.user.is_authenticated:
        # Prefer first_name, fallback to username or email
        display_name = request.user.first_name or request.user.username or request.user.email.split('@')[0]
    else:
        display_name = "Guest"
    return JsonResponse({
        'is_authenticated': request.user.is_authenticated,
        'username': display_name
    })


def homepage(request):
    faqs = FAQ.objects.all()[:4]  # Limit to 4 FAQs
    return render(request, 'chatbot/homepage.html', {'faqs': faqs})


class KnowledgeBase:
    def get_answer(self, user_message, is_voice=False):
        user_message_clean = user_message.lower().strip()
        logger.debug(f"Processing query: {user_message_clean}, is_voice={is_voice}")

        # Handle simple greetings explicitly
        greetings = ["hi", "hello", "hey", "hola"]
        if user_message_clean in greetings:
            return "Hello! How can I assist you today?", None

        # Split user query into words
        user_words = set(user_message_clean.split())
        if not user_words:
            return "Sorry, I didn't understand that. Could you please provide more details?", None

        key_words = {"payment", "account", "update", "app"}
        generic_words = {"issues", "queries", "how", "do"}

        best_match_score, best_match, matched_faq = 0, None, None

        # Use spaCy for similarity if available and for voice input
        if nlp and is_voice:
            user_doc = nlp(user_message_clean)
            for faq in FAQ.objects.all():
                faq_doc = nlp(faq.question.lower())
                similarity = user_doc.similarity(faq_doc)
                match_score = similarity * 10  # Scale to match word-based scoring
                logger.debug(
                    f"Voice similarity for '{user_message_clean}' with FAQ '{faq.question}': Similarity = {similarity}, Score = {match_score}")
                if match_score > best_match_score:
                    best_match_score = match_score
                    best_match = faq.answer
                    matched_faq = faq
        else:
            # Existing word-based matching
            for faq in FAQ.objects.all():
                faq_question = faq.question.lower()
                faq_words = set(faq_question.split())
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

        # Adjust min_score for voice input
        min_score = 0.5 if is_voice else 1
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

        logger.debug(f"No match for '{user_message_clean}': best_score={best_match_score}, min_score={min_score}")
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

    def get_response(self, user_message, session, is_voice=False):
        context = session.get('chat_context', {})
        logger.debug(f"Current context: {context}")

        if "weather" in user_message.lower():
            city = user_message.lower().replace("weather", "").strip()
            if not city:
                session['chat_context'] = {'intent': 'weather', 'awaiting': 'city'}
                session.modified = True
                return self.weather_service.get_weather(city), None
            return self.weather_service.get_weather(city), None
        elif context.get('intent') == 'weather' and context.get('awaiting') == 'city':
            city = user_message.strip()
            session['chat_context'] = {}
            session.modified = True
            return self.weather_service.get_weather(city), None
        elif "open" in user_message.lower() or "launch" in user_message.lower():
            app_name = user_message.lower().replace("open", "").replace("launch", "").strip()
            return self.app_launcher.launch(app_name), None
        else:
            return self.knowledge_base.get_answer(user_message, is_voice=is_voice)


chatbot_instance = Chatbot()


def chatbot_view(request):
    username = request.user.username if request.user.is_authenticated else "Guest"
    current_time = timezone.now().hour
    if 5 <= current_time < 12:
        time_greeting = "Good morning"
    elif 12 <= current_time < 17:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"
    welcome_message = f"{time_greeting}, {username}! How can I assist you with your FAQs today?"

    faqs = FAQ.objects.all()[:4]
    return render(request, "chatbot/chat.html", {
        "welcome_message": welcome_message,
        "faqs": faqs
    })


@login_required
def chatbot_home(request):
    username = request.user.username if request.user.is_authenticated else "Guest"
    current_time = timezone.now().hour
    if 5 <= current_time < 12:
        time_greeting = "Good morning"
    elif 12 <= current_time < 17:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"
    welcome_message = f"{time_greeting}, {username}! How can I assist you with your FAQs today?"

    faqs = FAQ.objects.all()[:4]
    return render(request, "chatbot/chat.html", {
        "welcome_message": welcome_message,
        "faqs": faqs
    })


@csrf_exempt
def get_response(request):
    start_time = time.time()
    if request.method != "POST":
        logger.error("Invalid request method: %s", request.method)
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        is_voice = data.get('is_voice', False)

        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        session = request.session

        # Initialize chat context
        if not session.get('chat_initialized'):
            session['chat_context'] = {'greeting_sent': False}
            session['chat_initialized'] = True
            session.modified = True

        context = session.get('chat_context', {})

        # Send personalized greeting on first load
        if not user_message and not context.get('greeting_sent'):
            current_time = timezone.now().hour
            time_greeting = (
                "Good morning" if 5 <= current_time < 12
                else "Good afternoon" if 12 <= current_time < 17
                else "Good evening"
            )
            username = "Guest"
            if request.user.is_authenticated:
                username = request.user.first_name or request.user.username or "User"
                logger.debug("Authenticated user: %s, first_name: %s", request.user.username, request.user.first_name)

            greeting = f"{time_greeting}, {username}! How can I assist you with your FAQs today?"
            session['chat_context'] = {'greeting_sent': True}
            session.modified = True
            try:
                session.save()
            except Exception as e:
                logger.error("Session save error: %s", str(e))
            logger.info("Sending greeting: %s", greeting)
            return JsonResponse({'response': greeting})

        # Handle escalation prompt response
        if context.get('intent') == 'escalation_prompt' and user_message.lower() in ["yes", "y"]:
            session['chat_context'] = {}
            session.modified = True
            try:
                session.save()
            except Exception as e:
                logger.error("Session save error: %s", str(e))
            response_data = {
                'response': "Please feel free to reach out for further assistance.",
                'escalate': True,
                'contact': {
                    'phone': CONTACT_PHONE,
                    'email': CONTACT_EMAIL
                }
            }
            logger.debug("Escalation confirmed: %s", response_data)
            return JsonResponse(response_data)

        # Handle user message
        response_data = {}
        matched_faq = None
        bot_response = None

        if user_message:
            # Try chatbot_instance first
            try:
                bot_response, matched_faq = chatbot_instance.get_response(user_message, session, is_voice=is_voice)
                if isinstance(bot_response, dict) and 'sub_faqs' in bot_response:
                    response_data = bot_response
                elif bot_response:
                    response_data = {'response': bot_response}
                else:
                    response_data = {
                        'response': "Sorry, I didn't understand that. Could you please provide more details?"}
                logger.debug("Chatbot response: %s, Matched FAQ: %s", bot_response, matched_faq)
            except Exception as e:
                logger.error("Chatbot instance error: %s", str(e))
                # Fallback to simple FAQ matching
                try:
                    # Match by question (case-insensitive)
                    faqs = FAQ.objects.filter(question__iexact=user_message)
                    if not faqs.exists():
                        # Broader search if exact match fails
                        faqs = FAQ.objects.filter(question__icontains=user_message)[:3]
                    if faqs.exists():
                        if faqs.count() == 1:
                            matched_faq = faqs.first()
                            bot_response = matched_faq.answer or "Here are related questions."
                            sub_faqs = [{'id': child.id, 'question': child.question} for child in
                                        matched_faq.children.all()]
                            response_data = {
                                'response': bot_response,
                                'sub_faqs': sub_faqs
                            }
                            logger.debug("Matched FAQ: %s, Sub-FAQs: %s", matched_faq.question, sub_faqs)
                        else:
                            sub_faqs = [{'id': faq.id, 'question': faq.question} for faq in faqs]
                            response_data = {
                                'response': "Here are related questions:",
                                'sub_faqs': sub_faqs
                            }
                            logger.debug("Multiple FAQs matched: %s", [faq.question for faq in faqs])
                    else:
                        bot_response = "Sorry, I didn't understand that. Could you please provide more details?"
                        response_data = {'response': bot_response}
                        logger.debug("No FAQ match for: %s", user_message)
                except Exception as e:
                    logger.error("FAQ query error: %s", str(e))
                    bot_response = "Sorry, I couldn't process your request."
                    response_data = {'response': bot_response}

            # Frustration detection
            greetings = ["hi", "hello", "hey", "hola"]
            is_greeting = user_message.lower().strip() in greetings
            if not is_greeting:
                frustration_signals = ["not helpful", "useless", "didn't work", "still confused"]
                is_frustrated = any(signal in user_message.lower() for signal in frustration_signals)
                session_key = session.session_key
                try:
                    recent_queries = QueryLog.objects.filter(
                        timestamp__gte=timezone.now() - timezone.timedelta(minutes=5),
                        session_key=session_key
                    ).order_by('-timestamp')
                    repeat_count = sum(
                        1 for q in recent_queries if q.query_text.lower().strip() == user_message.lower().strip()
                    )
                    unresolved_count = recent_queries.filter(unresolved=True).count()
                except Exception as e:
                    logger.warning("QueryLog error: %s, skipping frustration detection", str(e))
                    repeat_count = 0
                    unresolved_count = 0

                # Escalation logic
                escalate = is_frustrated or repeat_count >= 5 or unresolved_count >= 6
                if escalate:
                    bot_response = "It seems I couldn’t fully assist you. Would you like to contact support?"
                    session['chat_context'] = {'intent': 'escalation_prompt'}
                    session.modified = True
                    try:
                        session.save()
                    except Exception as e:
                        logger.error("Session save error: %s", str(e))
                    response_data = {
                        'response': bot_response,
                        'escalate': True
                    }
                    logger.info(
                        "Escalation triggered: Frustrated=%s, Repeats=%s, Unresolved=%s",
                        is_frustrated, repeat_count, unresolved_count
                    )

            # Log the query
            try:
                lead_keywords = ["how does this work", "tell me more", "what can you do", "interested", "details"]
                is_lead = any(keyword in user_message.lower() for keyword in lead_keywords)
                response_time = time.time() - start_time
                QueryLog.objects.create(
                    query_text=user_message,
                    timestamp=timezone.now(),
                    matched_faq=matched_faq,
                    unresolved=matched_faq is None or 'escalate' in response_data,
                    response_time=response_time,
                    is_lead=is_lead,
                    session_key=session_key
                )
            except Exception as e:
                logger.warning("Failed to log query: %s", str(e))

        # Clear escalation context if not escalating
        if not response_data.get('escalate') and context.get('intent') == 'escalation_prompt':
            session['chat_context'] = {}
            session.modified = True
            try:
                session.save()
            except Exception as e:
                logger.error("Session save error: %s", str(e))

        logger.debug("Response data: %s", response_data)
        return JsonResponse(response_data or {'response': "Sorry, I couldn't process your request."})

    except json.JSONDecodeError as e:
        logger.error("JSON decode error: %s", str(e))
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error("Unexpected error in get_response: %s", str(e))
        return JsonResponse({'error': 'Sorry, there was an error processing your request.'}, status=500)


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
    page = int(request.GET.get('page', 0)) + 1
    limit = int(request.GET.get('limit', 5))

    faqs = FAQ.objects.all().order_by('id')
    paginator = Paginator(faqs, limit)
    total_faqs = paginator.count

    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)

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
