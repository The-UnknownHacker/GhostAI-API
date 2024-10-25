from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import requests
from google.generativeai.types.safety_types import HarmBlockThreshold
import base64
from training_data import convo
from flask_pymongo import PyMongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import secrets


safety_settings_default = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
]

generation_config = {
    "temperature": 1.0,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 1000,
}





model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=generation_config,
    safety_settings=safety_settings_default
)

app = Flask(__name__)


mongo_url = 'mongodb+srv://ghostai:ghostai@ghostai.4bni5mt.mongodb.net/your_database_name?retryWrites=true&w=majority&appName=GhostAI'
app.config['MONGO_URI'] = mongo_url
mongo = PyMongo(app)  # Move this line to the global scope
client = MongoClient(mongo_url, server_api=ServerApi('1'))

# Define the path to the file containing valid API keys
VALID_API_KEYS_FILE = 'valid_api_keys.txt'
# Define your own API key for Google Generative AI service
GOOGLE_API_KEY = "Your API"

# Configure GhostAI with your API key
genai.configure(api_key=GOOGLE_API_KEY)

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    api_key = data.get('api_key')
    model = data.get('model')
    message = data.get('message')

    if not is_valid_api(api_key):
        return jsonify({'error': 'Invalid API key'}), 401

    if model not in ['img', 'chat']:
        return jsonify({'error': 'Invalid model type'}), 400

    if model == 'chat':
        response = generate_chat_response(message)
    elif model == 'img':
        response = generate_image_response(message)

    return jsonify(response)

def is_valid_api(api_key):
    with open('valid_api_keys.txt', 'r') as file:
        valid_api_keys = file.read().splitlines()
        return api_key in valid_api_keys


def generate_chat_response(message):
    return convo.send_message(message).text

def query(payload):
    API_URL = "https://frightened-dove-turtleneck-shirt.cyclic.app/proxy/https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    HEADERS = {"Authorization": "Bearer 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"}
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    return response.content

def generate_image_response(message):
    input_prompt = message  # Assuming 'message' contains the prompt
    payload = {"prompt": input_prompt, "aspect_ratio": "1:1"}

    try:
        # Call your existing function to query the AI model
        image_bytes = query({"inputs": input_prompt})

        # Convert the image bytes to a base64-encoded string
        image_data = base64.b64encode(image_bytes).decode('utf-8')

        # Return the base64-encoded image data
        return {'image_response': image_data}

    except Exception as e:
        # Handle exceptions, such as network errors or invalid responses
        return {'error': str(e)}
    


def checkuserlogin(username, password):
    user = mongo.db.users.find_one({'username': username, 'password': password})
    return user is not None


@app.route('/getkey', methods=['GET', 'POST'])
def getkey():
    if request.method == 'GET':
        # Display the login form
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if checkuserlogin(username, password):
            # Generate a random API key
            api_key = secrets.token_urlsafe(48)
            # Append the API key to the file
            with open('valid_api_keys.txt', 'a') as file:
                file.write(f"{api_key}\n")
            return jsonify({"Your API Key": api_key})
        else:
            return 'Invalid Credentials', 401
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
