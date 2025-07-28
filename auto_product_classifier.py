import json
import requests
import time
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AutoProductClassifier:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        
        # Product type mapping based on the table
        self.product_type_mapping = {
            "Nước ngọt có ga": "Các loại nước có gas, có vị ngọt, thường nhiều đường hoặc zero calorie",
            "Nước lọc / nước tinh khiết": "Nước uống không hương vị, không gas",
            "Nước tăng lực / Thức uống thể thao": "Có chứa điện giải, caffeine hoặc đường năng lượng cao",
            "Nước trái cây / trà": "Nước ép hoa quả, trà đóng chai, nước có vị tự nhiên",
            "Cà phê / Sữa / Đồ uống đặc biệt": "Các sản phẩm cà phê lon, sữa pha, đồ uống cao cấp",
            "Đồ uống có cồn (nếu có)": "Bia nhẹ, cocktail đóng lon hoặc các sản phẩm chứa cồn"
        }
        
    def load_products(self) -> List[Dict[str, Any]]:
        """Load products from JSON file"""
        try:
            with open('data/concatenated_products.json', 'r', encoding='utf-8') as f:
                products = json.load(f)
            return products
        except FileNotFoundError:
            print("Error: Products file not found!")
            return []
        except json.JSONDecodeError:
            print("Error: Invalid JSON file!")
            return []
    
    def create_prompt(self, products: List[Dict[str, Any]]) -> str:
        """Create prompt for Gemini API"""
        product_info = []
        for i, product in enumerate(products, 1):
            name = product.get('product_name', 'Unknown')
            description = product.get('description', '')
            ingredients = product.get('ingredients', [])
            
            product_info.append(f"""
Sản phẩm {i}: {name}
Mô tả: {description}
Thành phần: {', '.join(ingredients) if ingredients else 'Không có thông tin'}
""")
        
        prompt = f"""
Bạn là chuyên gia phân loại sản phẩm đồ uống của Coca-Cola. Hãy phân loại các sản phẩm sau vào một trong các nhóm sau:

1. Nước ngọt có ga - Các loại nước có gas, có vị ngọt, thường nhiều đường hoặc zero calorie
2. Nước lọc / nước tinh khiết - Nước uống không hương vị, không gas  
3. Nước tăng lực / Thức uống thể thao - Có chứa điện giải, caffeine hoặc đường năng lượng cao
4. Nước trái cây / trà - Nước ép hoa quả, trà đóng chai, nước có vị tự nhiên
5. Cà phê / Sữa / Đồ uống đặc biệt - Các sản phẩm cà phê lon, sữa pha, đồ uống cao cấp
6. Đồ uống có cồn (nếu có) - Bia nhẹ, cocktail đóng lon hoặc các sản phẩm chứa cồn

Các sản phẩm cần phân loại:
{''.join(product_info)}

QUAN TRỌNG: Bạn PHẢI trả về chính xác định dạng JSON sau, không có text nào khác:

{{
    "classifications": [
        {{
            "product_name": "Tên sản phẩm chính xác",
            "product_type": "Tên nhóm sản phẩm chính xác",
            "confidence": "Cao/Trung bình/Thấp",
            "reasoning": "Lý do phân loại ngắn gọn"
        }}
    ]
}}

Đảm bảo:
- Chỉ trả về JSON, không có text khác
- Tên sản phẩm phải chính xác như trong danh sách
- Tên nhóm sản phẩm phải chính xác như trong danh sách 6 nhóm
- JSON phải hợp lệ và có thể parse được
"""
        return prompt
    
    def call_gemini_api(self, prompt: str) -> Dict[str, Any]:
        """Call Gemini API"""
        headers = {
            "Content-Type": "application/json",
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        url = f"{self.base_url}?key={self.api_key}"
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            print(f"API Response Status: {response.status_code}")
            print(f"API Response Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if 'candidates' in result and len(result['candidates']) > 0:
                text_response = result['candidates'][0]['content']['parts'][0]['text']
                print(f"Raw text response: {text_response[:200]}...")
                
                # Try to extract JSON from the response
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
                    return json.loads(text_response)
                except json.JSONDecodeError:
                    # Try to find JSON in the response
                    import re
                    json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group())
                        except json.JSONDecodeError:
                            print(f"Failed to parse JSON from extracted text: {json_match.group()[:200]}...")
                            return None
                    else:
                        print(f"No JSON found in response: {text_response}")
                        return None
            else:
                print(f"Error: No candidates in response. Full response: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error calling Gemini API: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing API response JSON: {e}")
            print(f"Response content: {response.text[:500]}...")
            return None
    
    def process_batch(self, products: List[Dict[str, Any]], max_retries: int = 3) -> List[Dict[str, Any]]:
        """Process a batch of products with retry mechanism"""
        print(f"Processing batch of {len(products)} products...")
        
        for attempt in range(max_retries):
            try:
                prompt = self.create_prompt(products)
                result = self.call_gemini_api(prompt)
                
                if result and 'classifications' in result:
                    # Add product_type_description to each classification
                    for classification in result['classifications']:
                        product_type = classification.get('product_type', '')
                        classification['product_type_description'] = self.product_type_mapping.get(product_type, '')
                    
                    print(f"Successfully processed batch (attempt {attempt + 1})")
                    return result['classifications']
                else:
                    print(f"Invalid response from API (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        print("Retrying...")
                        time.sleep(2)
                    
            except Exception as e:
                print(f"Error processing batch (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    time.sleep(2)
        
        print("Failed to process batch after all retries")
        return []
    
    def classify_all_products(self, batch_size: int = 10) -> List[Dict[str, Any]]:
        """Classify all products in batches"""
        products = self.load_products()
        if not products:
            print("No products to classify")
            return []
        
        # Filter products with names
        products_with_names = [p for p in products if p.get('product_name')]
        print(f"Total products to classify: {len(products_with_names)}")
        
        all_classifications = []
        
        # Process in batches
        for i in range(0, len(products_with_names), batch_size):
            batch = products_with_names[i:i + batch_size]
            print(f"\nProcessing batch {i//batch_size + 1}/{(len(products_with_names) + batch_size - 1)//batch_size}")
            
            classifications = self.process_batch(batch)
            all_classifications.extend(classifications)
            
            # Add delay to avoid rate limiting
            if i + batch_size < len(products_with_names):
                print("Waiting 2 seconds before next batch...")
                time.sleep(2)
        
        return all_classifications
    
    def save_classifications(self, classifications: List[Dict[str, Any]], filename: str = "auto_classifications.json"):
        """Save classifications to file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(classifications, f, indent=2, ensure_ascii=False)
            print(f"Classifications saved to {filename}")
        except Exception as e:
            print(f"Error saving classifications: {e}")
    
    def create_products_with_types(self, classifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create products data with type classifications"""
        products = self.load_products()
        products_with_types = []
        
        # Create a mapping of product name to classification
        classification_map = {}
        for classification in classifications:
            product_name = classification.get('product_name', '')
            classification_map[product_name] = classification
        
        # Add classifications to original product data
        for product in products:
            product_name = product.get('product_name', '')
            if product_name in classification_map:
                classification = classification_map[product_name]
                product_with_type = product.copy()
                product_with_type['product_type'] = classification.get('product_type', '')
                product_with_type['product_type_description'] = classification.get('product_type_description', '')
                product_with_type['classification_confidence'] = classification.get('confidence', '')
                product_with_type['classification_reasoning'] = classification.get('reasoning', '')
                products_with_types.append(product_with_type)
            else:
                # Keep original product without classification
                products_with_types.append(product)
        
        return products_with_types
    
    def save_products_with_types(self, products_with_types: List[Dict[str, Any]], filename: str = "products_with_auto_types.json"):
        """Save products with type classifications"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(products_with_types, f, indent=2, ensure_ascii=False)
            print(f"Products with types saved to {filename}")
        except Exception as e:
            print(f"Error saving products with types: {e}")

def main():
    print("Auto Product Classifier using Gemini API")
    print("=" * 50)
    
    try:
        classifier = AutoProductClassifier()
        
        # Classify all products
        print("Starting automatic classification...")
        classifications = classifier.classify_all_products(batch_size=10)
        
        if classifications:
            print(f"\nSuccessfully classified {len(classifications)} products")
            
            # Save raw classifications
            classifier.save_classifications(classifications)
            
            # Create products with types
            products_with_types = classifier.create_products_with_types(classifications)
            classifier.save_products_with_types(products_with_types)
            
            # Print summary
            type_counts = {}
            for classification in classifications:
                product_type = classification.get('product_type', 'Unknown')
                type_counts[product_type] = type_counts.get(product_type, 0) + 1
            
            print("\nClassification Summary:")
            for product_type, count in type_counts.items():
                print(f"- {product_type}: {count} products")
            
            print(f"\nYou can now run 'python product_type_interface.py' to review the results!")
            
        else:
            print("No classifications were generated")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 