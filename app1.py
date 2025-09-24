import os
import json
from flask import Flask, request, session, jsonify, render_template, flash, redirect, url_for
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = Flask(__name__)
# A secret key is required for Flask session management
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

# Load the health data from the JSON file
try:
    with open('finalData.json', 'r', encoding='utf-8') as f:
        health_data = json.load(f)
except FileNotFoundError:
    print("ERROR: finalData.json not found. Please ensure the file exists.")
    health_data = {}  # Default to empty dict to avoid crashing

# Configure the Gemini API client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please set it.")

client = genai.Client(api_key=api_key)

# --- Load Data and Configuration ---

SUBSCRIBERS_FILE = 'broadcast_subscribers.json'

# Load Twilio credentials from environment variables
ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# It's critical that ACCOUNT_SID and AUTH_TOKEN are set. 
# If they are not found, the app can't connect to Twilio.
if not ACCOUNT_SID or not AUTH_TOKEN:
    print("ERROR: Twilio credentials ACCOUNT_SID and AUTH_TOKEN must be set in the environment.")
else:
    twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)


# Define the system prompt with the health data.
SYSTEM_PROMPT = f"""
You are a compassionate and expert health assistant chatbot. Your goal is to help users understand their health concerns.

You have access to a trusted dataset of health information:
{json.dumps(health_data)}

**Your Instructions:**

1.  **Prioritize Provided Data:** First, ALWAYS try to answer the user's query using the data provided above. Treat it as your primary source of truth.
2. If the user's query cannot be answered using the provided data, you must then attempt to answer it using your general knowledge. When doing so, you are required to:

Prioritize information from reliable public health sources like the World Health Organization (WHO) and national health ministries.

Add a clear disclaimer that the information is for informational purposes and comes from outside the chatbot's primary dataset. For example: "My primary dataset doesn't cover this, but based on general public health information...".
3.  **Act as an NLU:** Analyze the user's message to understand their intent (e.g., asking about a disease, symptoms, or prevention).
4.  **Engage in Conversation:** Do not just provide a generic answer. Ask clarifying questions to understand the user's situation better.
5.  **Deduce and Suggest:** Based on the conversation, if you can deduce a possible disease from the symptoms, provide information about that disease from the provided data.
6.  **Use External Knowledge as a Last Resort:** If the user's query cannot be answered using the provided data, you may use your internal knowledge. When doing so, you MUST prioritize information from trusted sources like the World Health Organization (WHO) and official Indian government health websites. State that you are providing information from outside the provided dataset.
7.  **Maintain a Natural Tone:** Your responses should be empathetic, clear, and easy to understand.
8.  **Do Not Provide a Diagnosis:** You are an AI assistant, not a doctor. Always remind the user to consult a qualified healthcare professional for a diagnosis.
"""

# --- Helper Functions ---

def get_subscribers():
    """Reads the list of subscribers from the JSON file."""
    if not os.path.exists(SUBSCRIBERS_FILE):
        return []
    try:
        with open(SUBSCRIBERS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def add_subscriber(number):
    """
    Adds a new subscriber to the list, avoiding duplicates.
    Returns True if the subscriber is new, False otherwise.
    """
    subscribers = get_subscribers()
    if number not in subscribers:
        subscribers.append(number)
        with open(SUBSCRIBERS_FILE, 'w') as f:
            json.dump(subscribers, f, indent=4)
        return True  # This is a new subscriber
    return False # This is an existing subscriber

def get_gemini_response(user_query, chat_history):
    """Gets a response from the Gemini model using a reconstructed chat session."""
    try:
        chat_session = client.chats.create(
            model='gemini-1.5-flash',
            history=chat_history,
            config={"system_instruction": SYSTEM_PROMPT}
        )
        response = chat_session.send_message(user_query)
        return response.text
    except Exception as e:
        print(f"An error occurred while getting Gemini response: {e}")
        return "I'm sorry, I encountered an error. Please try again later."

@app.route('/')
def hello():
    return render_template('home.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming WhatsApp messages and manages the chat session."""
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    add_subscriber(from_number) # Add subscriber, ignore if they already exist

    resp = MessagingResponse()
    msg = resp.message()

    chat_history = session.get('chat_history', [])
    
    lower_incoming_msg = incoming_msg.lower()

    if lower_incoming_msg in ['clear', 'reset', 'start over']:
        session.pop('chat_history', None)
        msg.body("Chat history cleared. How can I help you today?")
        return str(resp)

    if lower_incoming_msg in ['hi', 'hello', 'menu', 'start']:
        menu_text = (
            "Welcome to the Health Information Chatbot! How can I help you today?\n\n"
            "You can ask me about:\n"
            "🔹 Disease Information (Symptoms, Preventions)\n"
            "🔹 Vaccination Schedules\n"
            "🔹 First-Aid Help\n"
            "🔹 Emergency Contacts\n\n"
            "Just type your question naturally, for example, 'What are the symptoms of tuberculosis?'"
        )
        msg.body(menu_text)
    else:
        response_text = get_gemini_response(incoming_msg, chat_history)
        msg.body(response_text)
        
        chat_history.append({'role': 'user', 'parts': [{'text': incoming_msg}]})
        chat_history.append({'role': 'model', 'parts': [{'text': response_text}]})
        
        # Truncate history
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]
        
        session['chat_history'] = chat_history

    return str(resp)

@app.route('/status')
def status():
    return jsonify({"status": "OK"})

@app.route('/broadcast', methods=['GET'])
def show_broadcast_form():
    """Displays the HTML form for sending a broadcast.""" 
    return render_template('broadcast.html')

@app.route('/send-broadcast', methods=['POST'])
def handle_send_broadcast():
    """Handles the form submission and sends the broadcast message."""
    broadcast_message = request.form.get('message')
    if not broadcast_message:
        flash('Message cannot be empty.', 'error')
        return redirect(url_for('show_broadcast_form'))

    subscribers = get_subscribers()
    if not subscribers:
        flash('There are no subscribers to send a message to.', 'error')
        return redirect(url_for('show_broadcast_form'))

    sent_count = 0
    failed_count = 0

    if 'twilio_client' not in globals():
        flash('Twilio client is not configured. Check environment variables.', 'error')
        return redirect(url_for('show_broadcast_form'))

    for number in subscribers:
        try:
            twilio_client.messages.create(
                body=broadcast_message,
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=number
            )
            sent_count += 1
        except Exception as e:
            print(f"Failed to send to {number}: {e}")
            failed_count += 1

    flash(f'Broadcast sent! Messages sent: {sent_count}. Failed: {failed_count}.', 'success')
    return redirect(url_for('show_broadcast_form'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
