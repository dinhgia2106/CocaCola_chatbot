import json
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_api():
    """Test Gemini API with a simple request"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        return False
    
    base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    # Simple test prompt
    test_prompt = """
Bạn là chuyên gia phân loại sản phẩm đồ uống. Hãy phân loại sản phẩm sau:

Sản phẩm: Coca-Cola Original
Mô tả: Nước ngọt có gas, vị ngọt
Thành phần: Carbonated water, sugar, caramel color

Phân loại vào một trong các nhóm:
1. Nước ngọt có ga
2. Nước lọc / nước tinh khiết
3. Nước tăng lực / Thức uống thể thao
4. Nước trái cây / trà
5. Cà phê / Sữa / Đồ uống đặc biệt
6. Đồ uống có cồn (nếu có)

Trả về JSON:
{
    "classifications": [
        {
            "product_name": "Coca-Cola Original",
            "product_type": "Nước ngọt có ga",
            "confidence": "Cao",
            "reasoning": "Sản phẩm có gas, vị ngọt"
        }
    ]
}
"""
    
    headers = {
        "Content-Type": "application/json",
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": test_prompt
            }]
        }]
    }
    
    url = f"{base_url}?key={api_key}"
    
    try:
        print("Testing Gemini API...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        print(f"API Response Status: {response.status_code}")
        print(f"API Response Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if 'candidates' in result and len(result['candidates']) > 0:
            text_response = result['candidates'][0]['content']['parts'][0]['text']
            print(f"Raw text response: {text_response}")
            
            try:
                # Handle markdown code blocks
                text_response = text_response.strip()
                if text_response.startswith('```json'):
                    text_response = text_response[7:]  # Remove ```json
                if text_response.startswith('```'):
                    text_response = text_response[3:]  # Remove ```
                if text_response.endswith('```'):
                    text_response = text_response[:-3]  # Remove ```
                
                text_response = text_response.strip()
                json_result = json.loads(text_response)
                print("✅ JSON parsing successful!")
                print(f"Parsed result: {json.dumps(json_result, indent=2, ensure_ascii=False)}")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"Response text: {text_response}")
                return False
        else:
            print(f"❌ No candidates in response: {result}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling Gemini API: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing API response: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_api()
    if success:
        print("\n✅ API test successful! You can now run auto_product_classifier.py")
    else:
        print("\n❌ API test failed! Please check your API key and try again.") 