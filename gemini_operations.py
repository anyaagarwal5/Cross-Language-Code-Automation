# import google.generativeai as genai
# from config import gemini_cred

# def get_gemini_response(prompt):
#     genai.configure(api_key=gemini_cred["api_key"])
#     g_model = genai.GenerativeModel('gemini-1.5-pro')
#     chat = g_model.start_chat(history=[])
#     response = chat.send_message(prompt)
#     return response.text


import time
import google.generativeai as genai
from config import gemini_cred
from google.api_core.exceptions import ResourceExhausted

def get_gemini_response(prompt):
    genai.configure(api_key=gemini_cred["api_key"])
    g_model = genai.GenerativeModel('gemini-1.5-flash')

    retries = 3  # Number of retries
    delay = 2  # Initial delay in seconds

    for attempt in range(retries):
        try:
            chat = g_model.start_chat(history=[])
            response = chat.send_message(prompt)
            return response.text
        except ResourceExhausted:
            print(f"[Attempt {attempt+1}] Quota exceeded. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2  # Increase delay exponentially

    raise Exception("API quota exceeded. Try again later or check quota limits.")
