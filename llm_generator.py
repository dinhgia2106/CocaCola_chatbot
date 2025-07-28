import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Bạn có thể tái sử dụng logic API key từ IntentClassifier nếu muốn
# Ở đây chúng ta tạo một bản sao đơn giản
API_KEYS = [
    os.getenv('GEMINI_API_KEY_1'),
    os.getenv('GEMINI_API_KEY_2'), 
    os.getenv('GEMINI_API_KEY_3')
]
CURRENT_KEY_INDEX = 0
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def get_next_api_key() -> str:
    global CURRENT_KEY_INDEX
    key = API_KEYS[CURRENT_KEY_INDEX]
    CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(API_KEYS)
    return key

def generate_with_llm(prompt: str) -> str:
    """
    Gọi Gemini API (hoặc LLM khác) để sinh câu trả lời từ prompt.
    Trả về chuỗi text là câu trả lời.
    """
    api_keys = [
        os.getenv('GEMINI_API_KEY_1'),
        os.getenv('GEMINI_API_KEY_2'),
        os.getenv('GEMINI_API_KEY_3')
    ]
    url_base = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key="
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    for idx, api_key in enumerate(api_keys):
        if not api_key:
            continue
        url = url_base + api_key
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            if 'candidates' in data and data['candidates']:
                content = data['candidates'][0]['content']['parts'][0]['text']
                return content.strip()
            else:
                logging.error(f"Gemini API không trả về candidates hợp lệ. Response: {data}")
                continue
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logging.error(f"[llm_generator] API key {idx+1} bị 429 Too Many Requests, thử key tiếp theo...")
                continue
            logging.error(f"[llm_generator] Lỗi API call trong generator: {e}")
            continue
        except Exception as e:
            logging.error(f"[llm_generator] Lỗi gọi Gemini API sinh câu trả lời: {e}")
            continue
    return "[Lỗi khi gọi LLM để sinh câu trả lời hoặc hết quota các key]"