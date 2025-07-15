import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from emotion_model import load_emotion_model
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import json, random, requests
import joblib
from math import radians, sin, cos, sqrt, atan2
from flask import Flask, render_template
import re
import emoji
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__, template_folder='templates', static_folder='static')



CORS(app)  # Enable CORS for frontend-backend communication
@app.route('/')
def classic_theme():
    return render_template('index.html')

@app.route('/woodland_mix')
def woodland_mix_theme():
    return render_template('index2.html')

@app.route('/playful')
def playful_theme():
    return render_template('index3.html')

@app.route('/doctors')
def doctors_page():
    return render_template('doctors.html')

@app.route('/places_map')
def places_map_page():
    return render_template('places_map.html')


# Load trained emotion model and vectorizer
model, vectorizer = joblib.load('emotion_model.pkl')

# Load local jokes with associated emotions
with open('jokes.json', 'r', encoding='utf-8') as f:
    jokes = json.load(f)
def predict_emotion_and_joke(text):
    X = vectorizer.transform([text])
    emotion = model.predict(X)[0] if text else 'neutral'
    matched = [j for j in jokes if j.get('emotion') == emotion]
    joke = random.choice(matched if matched else jokes)
    return {'emotion': emotion, 'joke': joke['joke'], 'suggest_doctor': emotion in ['anxiety', 'depression']}

# ---------------------- Routes ----------------------

# 🧠 Predict emotion from input and return a joke
@app.route('/talk', methods=['POST'])
def talk():
    data = request.get_json()
    text = data.get('text', '')

    if text:
        X = vectorizer.transform([text])
        emotion = model.predict(X)[0]
    else:
        emotion = 'neutral'

    matched = [j for j in jokes if j.get('emotion') == emotion]
    joke = random.choice(matched if matched else jokes)

    response = {
        'emotion': emotion,
        'joke': joke['joke']
    }

    # Doctor Suggestion Flag
    if emotion in ['anxiety', 'depression']:
        response['suggest_doctor'] = True
    else:
        response['suggest_doctor'] = False

    return jsonify(response)
# nearby doctor
@app.route('/nearby_doctors', methods=['POST'])
def nearby_doctors():
    data = request.get_json()
    lat, lng = data['lat'], data['lng']
    api_key = 'AIzaSyByxAfy9rZaiWZ1rD9R_JkPbL5WNykpXoI'
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        'location': f'{lat},{lng}',
        'radius': 3000,
        'keyword': 'psychiatrist OR mental health',
        'key': api_key
    }
    resp = requests.get(url, params=params)
    return jsonify(resp.json())


# 😂 Live joke from icanhazdadjoke.com
@app.route('/live_joke', methods=['GET'])
def live_joke():
    headers = {'Accept': 'application/json'}
    try:
        resp = requests.get('https://icanhazdadjoke.com/', headers=headers, timeout=5)
        joke = resp.json().get('joke') if resp.status_code == 200 else "Couldn't fetch a joke right now!"
    except Exception:
        joke = "Network error fetching joke!"
    return jsonify(joke=joke)


# 📰 Live news from newsdata.io
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

@app.route('/live_news', methods=['GET'])
def live_news():
    url = f'https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&country=in&language=en'
    items = []

    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            for article in resp.json().get('results', []):
                items.append({
                    'title': article.get('title', 'No title'),
                    'url': article.get('link', '')
                })
        else:
            items.append({'title': "Couldn't fetch news.", 'url': ''})
    except Exception as e:
        print("News fetch error:", e)
        items.append({'title': "Network error fetching news.", 'url': ''})

    return jsonify(articles=items)

#llm chat --------------------------------------------------------------------------------------------------------------
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

def clean_reply(text):
    text = emoji.replace_emoji(text, replace='')
    text = re.sub(r'[*_~`]+', '', text)
    text = re.sub(r'\*(.*?)\*', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


@app.route('/llm_chat', methods=['POST'])
def llm_chat():
    data = request.get_json()
    messages = data.get("messages", [])

    if not messages or not isinstance(messages, list):
        return jsonify(reply="Say something first! 😅")

    # Inject hidden one-line + Ricky Gervais style instruction
    # Auto-detect greeting or normal chat, and inject matching hidden prompt
    user_input = messages[-1]["content"].lower()
    greeting_words = ["hello", "hi", "hey", "greetings", "good morning", "good evening"]

    user_input = messages[-1]["content"].lower()
    greeting_words = ["hello", "hi", "hey", "greetings", "good morning", "good evening"]

    if any(greet in user_input for greet in greeting_words):
        # Friendly, caring prompt for greetings with slight comedian inspiration
        hidden_instruction = (
            "(Reply in ONE LINE only, like a caring, friendly buddy in a casual conversation. "
            "Speak simply and clearly, with a warm, positive tone. "
            "Avoid overused metaphors or life advice. "
            "If appropriate, ask the user how they're feeling. "
            "Take slight inspiration from the friendly, playful sides of Ricky Gervais, James Acaster, or Russell Brand—but keep it light and cheerful.) "
        )
    else:
        # Dark, witty, sarcastic humor prompt for other messages
        hidden_instruction = (
            "(Reply in ONE LINE only, like Ricky Gervais, Jimmy Carr, James Acaster, or Russell Brand—dark, witty, psychological, sarcastic but secretly caring humor. "
            "Speak simply and clearly. "
            "NEVER mention AI, robots, digital life, or technology in your replies. "
            "When the user greets you, always start with 'Hello buddy!'.) "
        )

    # Inject hidden instruction before user's message
    messages[-1]["content"] = hidden_instruction + messages[-1]["content"]

    # Insert system prompt at the beginning, only once
    if not any(msg.get("role") == "system" for msg in messages):
        messages.insert(0, {
            "role": "system",
            "content": "Keep replies short, casual."
        })

    # Prepare payload for OpenRouter (Mistral Model)
    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": messages,
        "temperature": 0.75  # Balanced: less random, more focused humor
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"]
            reply = clean_reply(reply)
        else:
            reply = f"⚠️ API error {response.status_code}: {response.text}"
    except Exception as e:
        reply = f"Something went wrong: {str(e)}"

    # ✅ Backend safety suggestion (guaranteed)
    emotion_keywords = ["anxiety", "depressed", "sick","unwell"]
    if any(word in reply.lower() for word in emotion_keywords):
        reply += " By the way, you can also search for nearby doctors using Google Maps if you need support."

    return jsonify(reply=reply)

# 💡 Fan/Light smart command API
@app.route('/device_control', methods=['POST'])
def device_control():
    data = request.get_json()
    text = data.get("text", "").lower()

    device = action = None

    if "fan" in text:
        device = "fan"
        action = "on" if "on" in text or "start" in text else "off"
    elif "light" in text or "bulb" in text:
        device = "light"
        action = "on" if "on" in text or "start" in text else "off"
    elif any(word in text for word in ["ac", "a c", "air conditioner"]):
        device = "ac"
        action = "on" if "on" in text or "start" in text else "off"
    elif "tv" in text or "television" in text:
        device = "tv"
        action = "on" if "on" in text or "start" in text else "off"
    elif "music" in text or "music system" in text or "speaker" in text:
        device = "music"
        action = "on" if "on" in text or "start" in text or "play" in text else "off"
    elif "party" in text or "party mode" in text:
        device = "party"
        action = "on" if "on" in text or "start" in text or "activate" in text else "off"
    elif "curtain" in text:
        device = "curtain"
        action = "open" if "open" in text or "start" in text else "close"

    if device and action:
        return jsonify(success=True, device=device, action=action)
    else:
        return jsonify(success=False, message="No recognizable smart command")


#google map---------------------------------------------------------------------------------------------------------------------------------------


GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

def detect_emotion(text):
    X = vectorizer.transform([text])
    prediction = model.predict(X)
    return prediction[0]

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return round(R * c, 2)

def get_nearby_places(lat, lng, place_type):
    result = []
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=5000&type={place_type}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)
    data = response.json()

    for place in data.get('results', []):
        if 'geometry' in place and 'location' in place['geometry']:
            place_lat = place['geometry']['location']['lat']
            place_lng = place['geometry']['location']['lng']
            distance = calculate_distance(lat, lng, place_lat, place_lng)

            rating = place.get('rating', 0)
            if rating < 3.0:
                continue  # Filter low-rated places

            if any(excluded in place.get('types', []) for excluded in ['atm', 'bank']):
                continue  # Skip irrelevant types

            result.append({
                'name': place.get('name'),
                'address': place.get('vicinity', ''),
                'rating': rating,
                'distance_km': distance,
                'lat': place_lat,
                'lng': place_lng
            })
    return result



@app.route('/detect_emotion', methods=['POST'])
def emotion_route():
    data = request.get_json()
    text = data.get('text', '')
    emotion = detect_emotion(text)
    return jsonify({'emotion': emotion})

@app.route('/find_places', methods=['POST'])
def places_route():
    data = request.get_json()
    lat = data.get('lat')
    lng = data.get('lng')
    place_type = data.get('place_type')
    places = get_nearby_places(lat, lng, place_type)
    return jsonify(places)

    #-----------------------------------------------------------------------------------------------------------------------------------------------------


# 🌐 Optional: Control real devices (e.g., ESP32)
@app.route('/control_device', methods=['POST'])
def control_device():
    data = request.json
    command = data.get("command")

    try:
        if command == "turn on light":
            requests.get("http://192.168.1.42/light/on")
        elif command == "turn off fan":
            requests.get("http://192.168.1.42/fan/off")
        return jsonify({"status": "sent"})
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)})

#-----------------------------------------------------------------------------------------------------------------------
#webhook for google assistent___________________________________________________________________________________________
#-----------------------------------------------------------------------------------------------------------------------

session_store = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()
    session_id = req.get('session', '')
    intent = req.get('queryResult', {}).get('intent', {}).get('displayName', '')
    reply = "Sorry, I didn't understand that command."

    if intent == 'Detect Emotion and Tell Joke':
        user_text = req.get('queryResult', {}).get('queryText', '')
        resp = predict_emotion_and_joke(user_text)
        reply = f"Oh, {resp['emotion']} vibes detected! Here's a joke: {resp['joke']}"
        if resp['suggest_doctor']:
            reply += " You seem overwhelmed. Visit the doctors page on the app."

    elif intent == 'Live Joke':
        joke = live_joke().json['joke']
        reply = f"Here’s a fresh joke for you: {joke}"

    elif intent == 'Live News':
        headlines = [a['title'] for a in live_news().json['articles'][:5]]
        reply = "Here are the top news headlines: " + "; ".join(headlines)


    elif intent == 'Ask Funny Friend':

        user_text = req.get('queryResult', {}).get('queryText', '')

        # Retrieve previous chat history from context

        contexts = req.get('queryResult', {}).get('outputContexts', [])

        chat_history = []

        for ctx in contexts:

            if 'chat_history' in ctx['name']:
                chat_history = ctx.get('parameters', {}).get('history', [])

        chat_history.append({"role": "user", "content": user_text})

        with app.test_request_context(json={'messages': chat_history}):

            resp = json.loads(llm_chat().get_data(as_text=True))

        reply = resp['reply']

        chat_history.append({"role": "assistant", "content": reply})

        output_contexts = [

            {

                "name": f"{session_id}/contexts/chat_history",

                "lifespanCount": 20,

                "parameters": {

                    "history": chat_history

                }

            }

        ]

        return jsonify({

            "fulfillmentText": reply,

            "source": "funny-friend-webhook",

            "outputContexts": output_contexts

        })


    elif intent == 'Smart Device Control':
        user_text = req.get('queryResult', {}).get('queryText', '')
        with app.test_request_context(json={'text': user_text}):
            resp = json.loads(device_control().get_data(as_text=True))
        if resp['success']:
            reply = f"{resp['device'].capitalize()} has been turned {resp['action']}"
        else:
            reply = "Sorry, I couldn't understand the smart command."

    elif intent == 'Nearby Doctors':
        reply = "To find nearby doctors, please open the app and click the 'Find Nearby Doctors' button for the map and list."

    elif intent == 'Suggest Places by Emotion':
        reply = "To find places based on your emotion, open the app, enter your mood, and select a category for nearby places."

    return jsonify({"fulfillmentText": reply, "source": "funny-friend-webhook"})

# ------------------- Run App -------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)