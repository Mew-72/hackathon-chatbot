
# Health Chatbot Project

This project is a WhatsApp-based chatbot designed to provide users with quick access to health information and emergency services. It is built using Python, Flask, and the Twilio API, with a clear path toward integrating a Rasa NLU model for more advanced conversational AI.

## Current Features (v1.0 - Keyword-Based)

The chatbot is currently equipped with the following features, which operate based on keyword detection:

*   **WhatsApp Integration:** Connects with the Twilio API to send and receive messages on WhatsApp.
*   **Interactive Text-Based Menu:** When a new user sends a message, they receive a clear, text-based menu prompting them to select from "Symptoms," "Prevention," or "Nearest Clinic" to guide their query.
*   **Automatic Subscriber Management:** Automatically saves the phone numbers of new users to a `broadcast_subscribers.json` file for future broadcast messages.
*   **Keyword-Based Responses:** Provides information based on case-insensitive user input for several topics:
    *   **General Greetings:** Responds to "hi" or "hello" with the main menu.
    *   **Disease Information:** Provides a brief on specific diseases (e.g., "malaria").
    *   **Vaccination Schedules:** Gives details on vaccination schedules, sourced from the Indian Ministry of Health and Family Welfare (MoHFW).
    *   **First Aid:** Offers instructions for basic first aid (e.g., "first aid for minor cuts").
    *   **Emergency Contacts:** Lists verified emergency service numbers.
*   **Find a Nearby Hospital:** When a user asks for a "hospital" or "clinic," the chatbot sends a dynamic Google Maps link that opens on the user's phone and searches for nearby medical facilities based on their current location.
*   **Web-Based Broadcast System:** A simple web page at the `/broadcast` route allows an administrator to type and send a message to all subscribers via Twilio.

## Future Features (Roadmap - AI-Powered)

The next major step is to transition from a keyword-based system to a fully conversational AI using **Rasa**. The groundwork for this is already in place (`rasa/domain.yml`), and it will enable the following capabilities:

*   **Natural Language Understanding (NLU):** The chatbot will understand user intent beyond simple keywords, allowing for more natural conversations.
*   **Smarter, Context-Aware Dialogues:** The bot will be able to handle more complex queries by understanding intents and entities, such as:
    *   **Greeting and Closing:** `greet`, `goodbye`
    *   **General Health Advice:** `ask_hygiene`, `ask_vaccination`, `ask_doctor`
    *   **Specific Disease Queries:**
        *   `ask_disease_symptoms` (e.g., "What are the symptoms of malaria?")
        *   `ask_disease_prevention` (e.g., "How can I prevent cholera?")
    *   **Targeted Information:** `ask_vaccine_schedule`, `ask_first_aid`, `ask_emergency_contact`
*   **Entity Extraction:** The bot will recognize key pieces of information within a user's message, like `disease` and `language`, to provide more accurate responses.
*   **Full Admin Dashboard:** Expanding on the current broadcast page to create a comprehensive web dashboard for user management, analytics, and chatbot configuration.
*   **Appointment Booking:** Allowing users to schedule appointments at local clinics through the chatbot.
*   **Multilingual Support:** Adding the ability to respond in multiple languages based on user preference.
