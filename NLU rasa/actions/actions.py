# actions/actions.py
# Custom actions for multilingual health chatbot
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import json
import os

# Load health data
DATA_PATH = os.path.join(os.path.dirname(__file__), '../diseases.json')
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    HEALTH_DATA = json.load(f)

class ActionDiseaseSymptoms(Action):
    def name(self) -> Text:
        return "action_disease_symptoms"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        disease = tracker.get_slot("disease")
        language = tracker.get_slot("language") or "en"
        symptoms = HEALTH_DATA.get("diseases", {}).get(disease, {}).get("symptoms", {}).get(language)
        if symptoms:
            dispatcher.utter_message(text="\n".join(symptoms))
        else:
            dispatcher.utter_message(text={
                "en": "Sorry, I couldn't find symptoms for that disease/language.",
                "hi": "माफ़ कीजिए, उस बीमारी/भाषा के लिए लक्षण नहीं मिले।",
                "or": "ମାନ୍ୟ କରନ୍ତୁ, ସେଇ ରୋଗ/ଭାଷା ପାଇଁ ଲକ୍ଷଣ ମିଳିଲା ନାହିଁ।"
            }.get(language, "Sorry, I couldn't find symptoms for that disease/language."))
        return []

class ActionDiseasePrevention(Action):
    def name(self) -> Text:
        return "action_disease_prevention"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        disease = tracker.get_slot("disease")
        language = tracker.get_slot("language") or "en"
        prevention = HEALTH_DATA.get("diseases", {}).get(disease, {}).get("preventions", {}).get(language)
        if prevention:
            dispatcher.utter_message(text="\n".join(prevention))
        else:
            dispatcher.utter_message(text={
                "en": "Sorry, I couldn't find prevention tips for that disease/language.",
                "hi": "माफ़ कीजिए, उस बीमारी/भाषा के लिए बचाव जानकारी नहीं मिली।",
                "or": "ମାନ୍ୟ କରନ୍ତୁ, ସେଇ ରୋଗ/ଭାଷା ପାଇଁ ବଚାଉ ତଥ୍ୟ ମିଳିଲା ନାହିଁ।"
            }.get(language, "Sorry, I couldn't find prevention tips for that disease/language."))
        return []

class ActionGeneralInstruction(Action):
    def name(self) -> Text:
        return "action_general_instruction"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        instruction_type = tracker.get_slot("instruction_type")  # hygiene, vaccination, doctor_consultation
        language = tracker.get_slot("language") or "en"
        instruction = HEALTH_DATA.get("general_instructions", {}).get(instruction_type, {}).get(language)
        if instruction:
            dispatcher.utter_message(text=instruction)
        else:
            dispatcher.utter_message(text={
                "en": "Sorry, I couldn't find the requested information.",
                "hi": "माफ़ कीजिए, अनुरोधित जानकारी नहीं मिली।",
                "or": "ମାନ୍ୟ କରନ୍ତୁ, ଅନୁରୋଧିତ ତଥ୍ୟ ମିଳିଲା ନାହିଁ।"
            }.get(language, "Sorry, I couldn't find the requested information."))
        return []
