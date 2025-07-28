import json
import os
import logging
import re
from typing import Dict, Any, List

# Hãy đảm bảo các module này được import đúng
from intent_classifier import IntentClassifier
from vector_database import VectorDatabase
from llm_generator import generate_with_llm

logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self, vector_db_path: str = "vector_db/coca_cola_index", data_file: str = "data/final_product_data.json"):
        self.intent_classifier = IntentClassifier()
        self.vector_db = VectorDatabase()

        # Load vector DB
        if os.path.exists(f"{vector_db_path}.index"):
            self.vector_db.load_index(vector_db_path)
            logging.info("Đã load vector database")
        else:
            raise FileNotFoundError("Chưa có vector database, cần tạo trước.")

        # Load dữ liệu gốc để có thể LỌC và TÍNH TOÁN
        with open(data_file, "r", encoding="utf-8") as f:
            self.all_products_data = json.load(f)
        logging.info(f"Đã load {len(self.all_products_data)} sản phẩm gốc.")

    def generate_response(self, user_query: str) -> Dict[str, Any]:
        # 1. Phân loại Intent và Entities
        analysis = self.intent_classifier.classify_intent(user_query)
        intent = analysis.get("intent", "unknown")
        entities = analysis.get("entities", {})

        # 2. Định tuyến (Route) tác vụ dựa trên Intent
        if intent == 'greeting':
            response, relevant_items = self._handle_greeting()
        elif intent in ['list_by_product_type', 'list_by_brand', 'list_by_attribute']:
            response, relevant_items = self._handle_list_task(intent, entities)
        elif intent in ['find_min_attribute', 'find_max_attribute']:
            response, relevant_items = self._handle_extremum_task(intent, entities)
        elif intent == 'compare_two_products':
            response, relevant_items = self._handle_comparison_task(entities)
        else:
            # Các intent còn lại đều dùng semantic search
            response, relevant_items = self._handle_semantic_search(user_query, intent, entities)

        return {
            'query': user_query,
            'intent': intent,
            'entities': entities,
            'response': response,
            'relevant_chunks': relevant_items,
            'total_chunks_found': len(relevant_items)
        }
        
    # --- CÁC HÀM XỬ LÝ TÁC VỤ CHUYÊN BIỆT ---

    def _safe_extract_float(self, value: Any) -> float:
        """Hàm phụ trợ để trích xuất số float từ các định dạng dữ liệu khác nhau."""
        if value is None:
            return float('inf')
        if isinstance(value, (int, float)):
            return float(value)
        s_value = str(value).strip()
        match = re.search(r'^-?\d+(\.\d+)?', s_value)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return float('inf')
        return float('inf')

    def _handle_greeting(self):
        response = "Chào bạn! Tôi là trợ lý ảo của Coca-Cola. Tôi có thể giúp bạn tìm hiểu về các sản phẩm, thành phần, dinh dưỡng và nhiều thông tin khác. Bạn muốn biết gì?"
        return response, []

    def _handle_list_task(self, intent: str, entities: Dict):
        attribute = entities.get('attribute', '').lower()
        product_type = entities.get('product_type')
        brand_name = entities.get('brand_name')

        filtered_products = []
        # Lọc sản phẩm không đường
        if 'không đường' in attribute:
            for p in self.all_products_data:
                try:
                    sugars_value = p.get('nutrition_facts', {}).get('total_sugars', {}).get('value')
                    if sugars_value is not None and str(sugars_value).strip().startswith('0'):
                        filtered_products.append(p)
                except Exception:
                    continue
        elif product_type:
            filtered_products = [p for p in self.all_products_data if p.get('product_type') == product_type]
        elif brand_name:
            filtered_products = [p for p in self.all_products_data if brand_name.lower() in p.get('product_name', '').lower()]
        # Có thể thêm các logic lọc khác ở đây nếu cần

        if not filtered_products:
            return "Không tìm thấy sản phẩm phù hợp.", []

        product_names = [p.get('product_name') for p in filtered_products]
        prompt = f"""Người dùng muốn liệt kê các sản phẩm. Dưới đây là danh sách tìm được:
        {', '.join(product_names)}

        Dựa vào danh sách trên, hãy tạo một câu trả lời thân thiện. Nếu danh sách quá dài (hơn 10 sản phẩm), chỉ liệt kê một vài cái tên tiêu biểu và cho biết tổng số sản phẩm tìm thấy."""
        final_answer = generate_with_llm(prompt)
        return final_answer, filtered_products

    def _handle_extremum_task(self, intent: str, entities: Dict):
        user_attribute = entities.get("attribute", "")
        key_map = {'calo': 'calories', 'đường': 'total_sugars'}
        target_key = None
        for keyword, key in key_map.items():
            if keyword in user_attribute:
                target_key = key
                break
        if not target_key:
            return f"Xin lỗi, tôi không thể tìm kiếm theo thuộc tính '{user_attribute}'.", []
        valid_products = []
        for p in self.all_products_data:
            val = None
            if target_key == 'total_sugars':
                val = p.get('nutrition_facts', {}).get('total_sugars', {}).get('value')
            else:
                val = p.get('nutrition_facts', {}).get(target_key)
            val_float = self._safe_extract_float(val)
            if val_float != float('inf'):
                valid_products.append((p, val_float))
        if not valid_products:
            return "Không có dữ liệu phù hợp để so sánh.", []
        if "min" in intent:
            result_product, value = min(valid_products, key=lambda item: item[1])
        else:
            result_product, value = max(valid_products, key=lambda item: item[1])
        prompt = f"Sản phẩm có lượng {user_attribute} {'thấp nhất' if 'min' in intent else 'cao nhất'} là '{result_product.get('product_name')}' với giá trị {value}."
        final_answer = generate_with_llm(prompt)
        return final_answer, [result_product]

    def _handle_comparison_task(self, entities: Dict):
        product_names_query = entities.get("product_names", [])
        if len(product_names_query) < 2:
            return "Vui lòng cung cấp ít nhất hai sản phẩm để so sánh.", []
        products_to_compare = []
        found_products_set = set()
        for name_query in product_names_query:
            best_match = None
            for p in self.all_products_data:
                product_name_db = p.get('product_name', '')
                if product_name_db in found_products_set:
                    continue
                if name_query.lower() in product_name_db.lower() or \
                   all(word in product_name_db.lower() for word in name_query.lower().replace('-', ' ').split()):
                    best_match = p
                    break
            if best_match:
                products_to_compare.append(best_match)
                found_products_set.add(best_match['product_name'])
        if len(products_to_compare) < 2:
            return "Không tìm thấy đủ thông tin của cả hai sản phẩm để so sánh.", []
        contexts = []
        for p in products_to_compare:
            product_name = p['product_name']
            results = self.vector_db.search(
                query=f"Thông tin tổng hợp về {product_name}",
                k=1,
                metadata_filter={
                    'product_name': product_name,
                    'chunk_level': 2
                }
            )
            if results:
                contexts.append(results[0]['chunk']['content'])
            else:
                content = f"Tên sản phẩm: {p.get('product_name', '')}\n"
                content += f"Mô tả: {p.get('description', '')}\n"
                content += f"Thành phần: {p.get('ingredients', [])}\n"
                content += f"Dinh dưỡng: {p.get('nutrition_facts', {})}\n"
                contexts.append(content)
        if not all(contexts):
            return "Không thể tạo ngữ cảnh để so sánh.", []
        context_str = "\n\n---\n\n".join(contexts)
        prompt = f"""Dựa vào thông tin chi tiết của hai sản phẩm sau:
{context_str}
Hãy viết một đoạn văn so sánh hai sản phẩm này, tập trung vào những điểm khác biệt chính (ví dụ: calo, đường, caffeine, thành phần chính)."""
        final_answer = generate_with_llm(prompt)
        return final_answer, products_to_compare

    def _handle_semantic_search(self, user_query: str, intent: str, entities: Dict):
        metadata_filter = {}
        product_names = entities.get("product_names")
        if product_names:
            # Không filter nghiêm ngặt, ưu tiên sau khi search
            query_name = product_names[0].lower().replace('®', '')
        attribute = self.intent_classifier.get_attribute_for_intent(intent)
        if attribute:
            metadata_filter['attribute'] = attribute
        if product_names and not attribute:
            metadata_filter['chunk_level'] = 2
        results = self.vector_db.search(user_query, k=10, metadata_filter=metadata_filter)
        # Ưu tiên chunk khớp product_name
        if product_names and results:
            query_name_lower = product_names[0].lower().replace('®', '')
            prioritized_results = []
            other_results = []
            for res in results:
                chunk_product_name = res['chunk']['metadata'].get('product_name', '').lower().replace('®', '')
                if query_name_lower in chunk_product_name:
                    prioritized_results.append(res)
                else:
                    other_results.append(res)
            results = (prioritized_results + other_results)[:5]
        if not results:
            return "Xin lỗi, tôi không tìm thấy thông tin bạn cần.", []
        context = "\n\n---\n\n".join([res['chunk']['content'] for res in results])
        prompt = f"""Dựa vào các thông tin sau đây:
--- CONTEXT ---
{context}
--- END CONTEXT ---
Hãy trả lời thẳng vào câu hỏi của người dùng một cách ngắn gọn, không bình luận thêm về việc thiếu thông tin.
Câu hỏi: {user_query}
"""
        final_answer = generate_with_llm(prompt)
        return final_answer, results