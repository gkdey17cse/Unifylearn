# test_gemini.py
import google.generativeai as genai

# Direct test without environment variables
API_KEY = "AIzaSyCZA-_semc7d5ogZsN7wkKzKXGXTsk0dvw"
genai.configure(api_key=API_KEY)

try:
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    response = model.generate_content(
        "Say 'Hello World' in JSON format: {'message': 'Hello World'}"
    )
    print("SUCCESS! Gemini API is working.")
    print("Response:", response.text)
except Exception as e:
    print("ERROR:", e)
