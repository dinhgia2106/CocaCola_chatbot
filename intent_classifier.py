import os
import json
import requests
from typing import Dict, List, Any
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class IntentClassifier:
    def __init__(self):
        self.api_keys = [
            os.getenv('GEMINI_API_KEY_1'),
            os.getenv('GEMINI_API_KEY_2'), 
            os.getenv('GEMINI_API_KEY_3')
        ]
        self.current_key_index = 0
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        
    def get_next_api_key(self) -> str:
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    def classify_intent(self, user_question: str) -> Dict[str, Any]:
        system_prompt = """Bạn là một trợ lý phân tích truy vấn chuyên nghiệp cho chatbot của một công ty nước giải khát.
Nhiệm vụ của bạn là đọc câu hỏi của người dùng và phân loại ý định (intent) của họ, đồng thời trích xuất các thực thể quan trọng như tên sản phẩm.

Các intent có thể có là:
- get_ingredients: Hỏi về thành phần sản phẩm
- get_nutrition_facts: Hỏi về thông tin dinh dưỡng chung
- get_calories: Hỏi cụ thể về lượng calo
- get_sugar_content: Hỏi cụ thể về lượng đường
- check_caffeine: Hỏi về sự tồn tại của caffeine
- get_available_sizes: Hỏi về các kích cỡ/dung tích
- get_product_summary: Yêu cầu thông tin chung về sản phẩm
- compare_two_products: So sánh hai sản phẩm cụ thể
- product_inquiry: Câu hỏi mở về một sản phẩm
- list_by_product_type: Liệt kê sản phẩm theo loại
- list_by_brand: Liệt kê sản phẩm theo thương hiệu
- list_by_attribute: Liệt kê sản phẩm theo đặc tính
- list_by_country: Liệt kê sản phẩm theo quốc gia
- explain_category: Yêu cầu giải thích về một loại
- find_min_attribute: Tìm sản phẩm có giá trị thuộc tính nhỏ nhất (ít nhất, thấp nhất)
- find_max_attribute: Tìm sản phẩm có giá trị thuộc tính lớn nhất (nhiều nhất, cao nhất)
- greeting: Chào hỏi, trò chuyện thông thường

QUY TẮC QUAN TRỌNG:
- Nếu câu hỏi có từ "ít nhất", "thấp nhất", "nhỏ nhất", hãy dùng intent "find_min_attribute".
- Nếu câu hỏi có từ "nhiều nhất", "cao nhất", "lớn nhất", hãy dùng intent "find_max_attribute".
- Nếu người dùng hỏi về một thương hiệu (Coca-Cola, Fanta, Sprite), hãy dùng intent "list_by_brand".
- Khi trích xuất "product_names", hãy cố gắng trả về tên đầy đủ và chính xác nhất có thể, ví dụ "Coke Zero" nên là "Coca-Cola Zero Sugar".

Ví dụ 1:
Người dùng: "Thành phần của Fanta Cam là gì?"
JSON:
{
  "intent": "get_ingredients",
  "entities": {
    "product_names": ["Fanta Orange"]
  }
}

Ví dụ 2:
Người dùng: "So sánh Coca-Cola Original và Coke Zero."
JSON:
{
  "intent": "compare_two_products",
  "entities": {
    "product_names": ["Coca-Cola Original", "Coca-Cola Zero Sugar"]
  }
}

Ví dụ 3:
Người dùng: "Liệt kê các sản phẩm không đường."
JSON:
{
  "intent": "list_by_attribute",
  "entities": {
    "attribute": "không đường"
  }
}

Ví dụ 4:
Người dùng: "Danh sách các sản phẩm Coca-Cola"
JSON:
{
  "intent": "list_by_brand",
  "entities": {
    "brand_name": "Coca-Cola"
  }
}

Ví dụ 5:
Người dùng: "tôi cần nước thể thao"
JSON:
{
  "intent": "list_by_product_type",
  "entities": {
    "product_type": "Nước tăng lực / Thức uống thể thao"
  }
}

Ví dụ 6:
Người dùng: "Sản phẩm nào ít calo nhất?"
JSON:
{
  "intent": "find_min_attribute",
  "entities": {
    "attribute": "ít calo nhất"
  }
}

Ví dụ 7:
Người dùng: "Nước nào nhiều đường nhất?"
JSON:
{
  "intent": "find_max_attribute",
  "entities": {
    "attribute": "nhiều đường nhất"
  }
}

Bây giờ, hãy phân tích câu hỏi dưới đây.

Người dùng: {user_question}"""

        # Escape dấu { và } trong user_question để tránh lỗi format
        safe_user_question = user_question.replace('{', '{{').replace('}', '}}')
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": system_prompt.replace("{user_question}", safe_user_question)
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "topK": 1,
                "topP": 1,
                "maxOutputTokens": 1000
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        for attempt in range(len(self.api_keys)):
            try:
                api_key = self.get_next_api_key()
                url = f"{self.base_url}?key={api_key}"
                
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # Trích xuất JSON từ response
                    try:
                        start_idx = content.find('{')
                        end_idx = content.rfind('}') + 1
                        if start_idx != -1 and end_idx > start_idx:
                            json_str = content[start_idx:end_idx]
                            try:
                                return json.loads(json_str)
                            except Exception as e:
                                logger.error(f"Lỗi parse JSON: {e}\nContent trả về: {content}")
                                continue
                        else:
                            logger.error(f"Không tìm thấy JSON trong response. Content: {content}")
                            continue
                    except Exception as e:
                        logger.error(f"Lỗi khi xử lý response từ Gemini: {e}\nContent: {content}")
                        continue
            except requests.exceptions.RequestException as e:
                logger.error(f"Lỗi API call với key {attempt + 1}: {e}")
                continue
        # Fallback nếu tất cả API keys đều lỗi hoặc không parse được JSON
        logger.error(f"Không phân tích được intent cho câu hỏi: {user_question}")
        return {
            "intent": "unknown",
            "entities": {}
        }
    
    def get_chunk_level_for_intent(self, intent: str) -> int:
        level_1_intents = [
            "get_ingredients", "get_nutrition_facts", "get_calories", 
            "get_sugar_content", "check_caffeine", "get_available_sizes"
        ]
        level_2_intents = [
            "get_product_summary", "compare_two_products", "product_inquiry"
        ]
        level_3_intents = [
            "list_by_product_type", "list_by_attribute", "list_by_country", 
            "explain_category"
        ]
        if intent in level_1_intents:
            return 1
        elif intent in level_2_intents:
            return 2
        elif intent in level_3_intents:
            return 3
        else:
            return 2
    
    def get_attribute_for_intent(self, intent: str) -> str:
        intent_to_attribute = {
            "get_ingredients": "ingredients",
            "get_nutrition_facts": "nutrition_facts",
            "get_calories": "nutrition_facts",
            "get_sugar_content": "nutrition_facts",
            "check_caffeine": "ingredients",
            "get_available_sizes": "available_sizes"
        }
        return intent_to_attribute.get(intent, "")

def main():
    classifier = IntentClassifier()
    test_questions = [
        "Thành phần của Coca-Cola Original là gì?",
        "So sánh Coca-Cola Original và Coke Zero",
        "Liệt kê các sản phẩm không đường",
        "Coca-Cola Original có bao nhiêu calo?",
        "Chào bạn"
    ]
    for question in test_questions:
        result = classifier.classify_intent(question)
        chunk_level = classifier.get_chunk_level_for_intent(result.get('intent', ''))
        print(f"\nCâu hỏi: {question}")
        print(f"Intent: {result.get('intent', 'unknown')}")
        print(f"Entities: {result.get('entities', {})}")
        print(f"Chunk level: {chunk_level}")

if __name__ == "__main__":
    main() 