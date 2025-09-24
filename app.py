import json
import os
from flask import Flask, request, jsonify, render_template, flash, redirect, url_for
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# --- Load Data and Configuration ---

with open('diseases.json') as f:
    diseases_data = json.load(f)

with open('basic-first-aid-emergency.json') as f:
    first_aid_data = json.load(f)

with open('vaccination.json') as f:
    vaccination_data = json.load(f)

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
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

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

def get_welcome_message():
    """Generates the welcome message text with the menu."""
    response_text = "Welcome to the Health Chatbot!\n"
    response_text += "You can ask me about:\n"
    response_text += "- A specific disease (e.g., 'malaria')\n"
    response_text += "- Vaccination information\n"
    response_text += "- First aid for a condition\n"
    response_text += "- Emergency contacts\n"
    response_text += "- Nearby hospitals or clinics"
    return response_text

# --- Core Chatbot & API Routes ---

@app.route('/')
def hello():
    # return "The server is running! Navigate to /broadcast to send a message."
    return render_template('home.html')

@app.route('/status')
def status():
    return jsonify({"status": "OK"})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming WhatsApp messages from Twilio."""
    resp = MessagingResponse()
    msg = resp.message()
    
    from_number = request.values.get('From', '')
    is_new_user = False
    if from_number:
        is_new_user = add_subscriber(from_number)

    # If it's a new user, send the welcome message regardless of their input
    if is_new_user:
        msg.body(get_welcome_message())
    else:
        # For existing users, process their message as usual
        incoming_msg = request.values.get('Body', '').lower()

        if 'hi' in incoming_msg or 'hello' in incoming_msg:
            msg.body(get_welcome_message())

        elif 'hospital' in incoming_msg or 'clinic' in incoming_msg or 'health center' in incoming_msg:
            response_text = "To find a hospital or health center near you, open this link on your phone:\n\n"
            response_text += "https://www.google.com/maps/search/?api=1&query=hospital+near+me"
            msg.body(response_text)
        
        elif 'vaccine' in incoming_msg or 'vaccination' in incoming_msg:
            response_text = "Here is the vaccination information:\n\n"
            for vaccine in vaccination_data['vaccination_schedule']:
                response_text += f"*Vaccine:* {vaccine['vaccine_name']}\n"
                response_text += f"*Prevents:* {vaccine['disease_prevented']}\n"
                response_text += f"*Schedule:* {vaccine['schedule']}\n\n"
            msg.body(response_text)

        elif 'first aid' in incoming_msg:
            found = False
            for condition in first_aid_data['first_aid']:
                if condition['condition'].lower() in incoming_msg:
                    response_text = f"First aid for {condition['condition']}:\n"
                    for step in condition['steps']:
                        response_text += f"- {step}\n"
                    if 'warning' in condition:
                        response_text += f"\n*Warning:* {condition['warning']}"
                    msg.body(response_text)
                    found = True
                    break
            if not found:
                response_text = "What first aid information do you need?\n"
                for condition in first_aid_data['first_aid']:
                    response_text += f"- {condition['condition']}\n"
                msg.body(response_text)

        elif 'emergency' in incoming_msg or 'emergency contacts' in incoming_msg:
            response_text = "*Emergency Contacts:*\n"
            for contact in first_aid_data['emergency_contacts']:
                response_text += f"- {contact['service']}: {contact['number']}\n"
            msg.body(response_text)

        else:
            found_disease = False
            for disease in diseases_data['disease_symptoms']:
                if disease['disease_name'].lower() in incoming_msg:
                    response_text = f"*About {disease['disease_name']}:*\n"
                    response_text += "\n*Common Symptoms:*\n"
                    for symptom in disease['common_symptoms']:
                        response_text += f"- {symptom}\n"
                    response_text += "\n*Prevention Methods:*\n"
                    for category in disease['prevention_methods']:
                        response_text += f"  *{category['category']}:*\n"
                        for method in category['methods']:
                            response_text += f"  - {method}\n"
                    msg.body(response_text)
                    found_disease = True
                    break
            if not found_disease:
                fallback_message = "I'm sorry, I don't understand. Say 'hi' for the main menu. You can also ask for 'nearby hospitals'."
                msg.body(fallback_message)

    return str(resp)

# --- Web Broadcast Routes ---

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

    # Ensure the client is initialized before trying to use it
    if 'client' not in globals():
        flash('Twilio client is not configured. Check environment variables.', 'error')
        return redirect(url_for('show_broadcast_form'))

    for number in subscribers:
        try:
            client.messages.create(
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

# --- Main Execution ---

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)