#!/usr/bin/env python3
"""
Demo hệ thống RAG Coca-Cola Chatbot
"""

import os
import sys
import logging
from rag_system import RAGSystem
from vector_database import create_vector_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_system():
    """Thiết lập hệ thống"""
    print("COCA-COLA RAG SYSTEM DEMO")
    print("=" * 50)
    
    # Kiểm tra chunks
    if not os.path.exists("chunks/all_chunks.json"):
        print("Chưa có chunks. Chạy chunking_system.py trước.")
        return False
    
    # Kiểm tra vector database
    if not os.path.exists("vector_db/coca_cola_index.index"):
        print("Tạo vector database...")
        try:
            create_vector_database(index_type="IndexFlatL2")
            print("Đã tạo xong vector database!")
        except Exception as e:
            print(f"Lỗi tạo vector database: {e}")
            return False
    
    return True

def run_demo():
    """Chạy demo với các câu hỏi mẫu"""
    print("\n" + "=" * 50)
    print("DEMO CÁC CÂU HỎI MẪU:")
    print("=" * 50)
    
    # Khởi tạo hệ thống RAG
    rag_system = RAGSystem()
    
    # Danh sách câu hỏi demo
    demo_questions = [
        "Chào bạn",
        "Thành phần của Coca-Cola Original là gì?",
        "Coca-Cola Original có bao nhiêu calo?",
        "Coca-Cola Original có caffeine không?",
        "So sánh Coca-Cola Original và Coke Zero",
        "Liệt kê các sản phẩm không đường",
        "Các kích cỡ có sẵn của Coca-Cola Original",
        "Thông tin dinh dưỡng của Sprite",
        "Danh sách các sản phẩm Coca-Cola",
        "Sản phẩm nào ít calo nhất?"
    ]
    
    for i, question in enumerate(demo_questions, 1):
        print(f"\n{i}. Câu hỏi: {question}")
        print("-" * 50)
        
        try:
            logger.info(f"[DEBUG] Đang xử lý câu hỏi: {question}")
            result = rag_system.generate_response(question)
            logger.info(f"[DEBUG] Kết quả intent: {result.get('intent')}, entities: {result.get('entities')}")
            
            print(f"Intent: {result['intent']}")
            print(f"Entities: {result['entities']}")
            print(f"Trả lời: {result['response']}")
            print(f"Tìm thấy {result['total_chunks_found']} thông tin liên quan")
            
            # Hiển thị chunks được sử dụng
            if result['relevant_chunks']:
                print("\nThông tin liên quan được sử dụng:")
                for item in result['relevant_chunks'][:2]:
                    if isinstance(item, dict) and 'chunk' in item: # Nếu là kết quả từ search
                        print(f"  - [Chunk] Score: {item['score']:.2f}, Product: {item['chunk']['metadata'].get('product_name')}")
                    elif isinstance(item, dict) and 'product_name' in item: # Nếu là sản phẩm gốc
                        print(f"  - [Sản phẩm] {item.get('product_name')}")
                    else:
                        print(f"  - [Khác] {str(item)[:80]}")
            
        except Exception as e:
            logger.error(f"[EXCEPTION] {e}", exc_info=True)
            print(f"Lỗi: {e}")
        
        print("=" * 50)

def run_interactive():
    """Chế độ tương tác"""
    print("\n" + "=" * 50)
    print("CHẾ ĐỘ TƯƠNG TÁC")
    print("Nhập 'quit' để thoát, 'help' để xem trợ giúp")
    print("=" * 50)
    
    # Khởi tạo hệ thống RAG
    rag_system = RAGSystem()
    
    while True:
        try:
            user_input = input("\nBạn: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'thoát']:
                print("Tạm biệt!")
                break
            
            if user_input.lower() == 'help':
                print("\nCác loại câu hỏi bạn có thể hỏi:")
                print("- Hỏi về thành phần: 'Thành phần của Coca-Cola Original là gì?'")
                print("- Hỏi về dinh dưỡng: 'Coca-Cola Original có bao nhiêu calo?'")
                print("- So sánh sản phẩm: 'So sánh Coca-Cola Original và Coke Zero'")
                print("- Liệt kê sản phẩm: 'Liệt kê các sản phẩm không đường'")
                print("- Hỏi về kích cỡ: 'Các kích cỡ có sẵn của Coca-Cola Original'")
                continue
            
            if not user_input:
                continue
            
            print("Đang xử lý...")
            result = rag_system.generate_response(user_input)
            
            print(f"\nBot: {result['response']}")
            print(f"\n[Debug] Intent: {result['intent']}")
            print(f"[Debug] Tìm thấy {result['total_chunks_found']} chunks")
            
        except KeyboardInterrupt:
            print("\nTạm biệt!")
            break
        except Exception as e:
            logger.error(f"[EXCEPTION] {e}", exc_info=True)
            print(f"Lỗi: {e}")

def main():
    """Hàm chính"""
    if not setup_system():
        return
    
    # Chạy demo
    run_demo()
    
    # Hỏi người dùng có muốn chạy chế độ tương tác không
    print("\n" + "=" * 50)
    choice = input("Bạn có muốn chạy chế độ tương tác? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes', 'có']:
        run_interactive()
    else:
        print("Demo hoàn thành!")

if __name__ == "__main__":
    main() 