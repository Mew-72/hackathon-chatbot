# broadcast.py
#
# A command-line tool to send WhatsApp broadcast messages to all subscribers.

import json
import os
from twilio.rest import Client
from dotenv import load_dotenv

# Initialize the environment variables
load_dotenv()

# Subscriber numbers file
SUBSCRIBERS_FILE = 'broadcast_subscribers.json'

# Twilio account credentials (replace with your own)
# It is recommended to use environment variables for these
ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
TWILIO_PHONE_NUMBER = f'whatsapp:{os.getenv("TWILIO_PHONE_NUMBER")}'  # WhatsApp sandbox number

# Initialize the Twilio client
client = Client(ACCOUNT_SID, AUTH_TOKEN)

def get_subscribers():
    """Reads the list of subscribers from the JSON file."""
    try:
        with open(SUBSCRIBERS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Error: Could not find or read {SUBSCRIBERS_FILE}. Please ensure it exists and is a valid JSON file.")
        return []

def send_broadcast(broadcast_message):
    """
    Sends a broadcast message to all subscribers.
    """
    subscribers = get_subscribers()
    if not subscribers:
        print("There are no subscribers to send a broadcast to.")
        return

    print(f"Sending broadcast to {len(subscribers)} subscribers...")
    for number in subscribers:
        try:
            # The 'from_' number needs to be a WhatsApp-enabled Twilio number
            # and subscribers' numbers should be in 'whatsapp:<E.164 format>'
            message = client.messages.create(
                body=broadcast_message,
                from_=TWILIO_PHONE_NUMBER,
                to=number
            )
            print(f"Message sent to {number}: {message.sid}")
        except Exception as e:
            print(f"Failed to send message to {number}: {e}")

if __name__ == "__main__":
    print("WhatsApp Broadcast Tool")
    print("-----------------------")
    
    # Use a raw string for multi-line input to avoid issues
    print("Enter your broadcast message. Press Ctrl+D (or Ctrl+Z on Windows) when you are finished.")
    
    message_lines = []
    try:
        while True:
            line = input()
            message_lines.append(line)
    except EOFError:
        pass

    message_to_send = "\n".join(message_lines).strip()

    if message_to_send:
        # Confirm before sending
        print("\n--- MESSAGE PREVIEW ---")
        print(message_to_send)
        print("-----------------------")
        confirm = input("Are you sure you want to send this message to all subscribers? (y/n): ").strip().lower()
        if confirm == 'y':
            send_broadcast(message_to_send)
            print("Broadcast finished.")
        else:
            print("Broadcast cancelled.")
    else:
        print("Broadcast message cannot be empty. Exiting.")
