from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from rag_system import RAGSystem
from vector_database import create_vector_database

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Cho phép CORS

# Khởi tạo hệ thống RAG
rag_system = None

def initialize_rag_system():
    """Khởi tạo hệ thống RAG"""
    global rag_system
    
    try:
        # Kiểm tra vector database
        if not os.path.exists("vector_db/coca_cola_index.index"):
            logger.info("Tạo vector database...")
            create_vector_database(index_type="IndexFlatL2")
            logger.info("Đã tạo xong vector database!")
        
        # Khởi tạo RAG system
        rag_system = RAGSystem()
        logger.info("Đã khởi tạo RAG system thành công!")
        return True
        
    except Exception as e:
        logger.error(f"Lỗi khởi tạo RAG system: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'rag_system_ready': rag_system is not None
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint cho chat"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Thiếu trường message trong request'
            }), 400
        
        message = data['message'].strip()
        
        if not message:
            return jsonify({
                'error': 'Message không được để trống'
            }), 400
        
        # Kiểm tra RAG system
        if rag_system is None:
            return jsonify({
                'error': 'RAG system chưa sẵn sàng'
            }), 503
        
        # Xử lý câu hỏi
        logger.info(f"Xử lý câu hỏi: {message}")
        result = rag_system.generate_response(message)
        
        return jsonify({
            'success': True,
            'query': result['query'],
            'response': result['response'],
            'intent': result['intent'],
            'entities': result['entities'],
            'total_chunks_found': result['total_chunks_found'],
            'relevant_chunks': [
                (
                    {
                        'rank': item['rank'],
                        'score': item['score'],
                        'metadata': item['chunk']['metadata'],
                        'content_preview': item['chunk']['content'][:200] + '...' if len(item['chunk']['content']) > 200 else item['chunk']['content']
                    }
                    if isinstance(item, dict) and 'rank' in item and 'chunk' in item
                    else
                    {
                        'product_name': item.get('product_name'),
                        'description': item.get('description', ''),
                        'nutrition_facts': item.get('nutrition_facts', {}),
                        'ingredients': item.get('ingredients', [])
                    }
                    if isinstance(item, dict) and 'product_name' in item
                    else str(item)
                )
                for item in result['relevant_chunks']
            ]
        })
        
    except Exception as e:
        logger.error(f"Lỗi xử lý chat: {e}")
        return jsonify({
            'error': f'Lỗi xử lý: {str(e)}'
        }), 500

@app.route('/api/search', methods=['POST'])
def search():
    """API endpoint cho tìm kiếm semantic"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'error': 'Thiếu trường query trong request'
            }), 400
        
        query = data['query'].strip()
        k = data.get('k', 5)  # Số kết quả trả về, mặc định 5
        
        if not query:
            return jsonify({
                'error': 'Query không được để trống'
            }), 400
        
        # Kiểm tra RAG system
        if rag_system is None:
            return jsonify({
                'error': 'RAG system chưa sẵn sàng'
            }), 503
        
        # Tìm kiếm semantic
        logger.info(f"Tìm kiếm semantic: {query}")
        results = rag_system.vector_db.search(query, k=k)
        
        return jsonify({
            'success': True,
            'query': query,
            'results': [
                {
                    'rank': result['rank'],
                    'score': result['score'],
                    'metadata': result['chunk']['metadata'],
                    'content': result['chunk']['content']
                }
                for result in results
            ]
        })
        
    except Exception as e:
        logger.error(f"Lỗi tìm kiếm: {e}")
        return jsonify({
            'error': f'Lỗi tìm kiếm: {str(e)}'
        }), 500

@app.route('/api/intent', methods=['POST'])
def classify_intent():
    """API endpoint cho phân loại intent"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Thiếu trường message trong request'
            }), 400
        
        message = data['message'].strip()
        
        if not message:
            return jsonify({
                'error': 'Message không được để trống'
            }), 400
        
        # Kiểm tra RAG system
        if rag_system is None:
            return jsonify({
                'error': 'RAG system chưa sẵn sàng'
            }), 503
        
        # Phân loại intent
        logger.info(f"Phân loại intent: {message}")
        classification = rag_system.intent_classifier.classify_intent(message)
        
        return jsonify({
            'success': True,
            'message': message,
            'intent': classification.get('intent', 'unknown'),
            'entities': classification.get('entities', {}),
            'chunk_level': rag_system.intent_classifier.get_chunk_level_for_intent(classification.get('intent', ''))
        })
        
    except Exception as e:
        logger.error(f"Lỗi phân loại intent: {e}")
        return jsonify({
            'error': f'Lỗi phân loại intent: {str(e)}'
        }), 500

@app.route('/api/system-info', methods=['GET'])
def system_info():
    """API endpoint cho thông tin hệ thống"""
    try:
        if rag_system is None:
            return jsonify({
                'error': 'RAG system chưa sẵn sàng'
            }), 503
        
        # Thông tin vector database
        vdb_info = {
            'total_vectors': rag_system.vector_db.index.ntotal if rag_system.vector_db.index else 0,
            'index_type': type(rag_system.vector_db.index).__name__ if rag_system.vector_db.index else None
        }
        
        # Thông tin chunks
        chunks_info = {
            'total_chunks': len(rag_system.vector_db.chunks) if rag_system.vector_db.chunks else 0
        }
        
        return jsonify({
            'success': True,
            'vector_database': vdb_info,
            'chunks': chunks_info,
            'model_name': 'paraphrase-multilingual-MiniLM-L12-v2'
        })
        
    except Exception as e:
        logger.error(f"Lỗi lấy thông tin hệ thống: {e}")
        return jsonify({
            'error': f'Lỗi lấy thông tin hệ thống: {str(e)}'
        }), 500

@app.route('/', methods=['GET'])
def index():
    """Trang chủ với hướng dẫn API"""
    return jsonify({
        'message': 'Coca-Cola RAG API',
        'version': '1.0.0',
        'endpoints': {
            'GET /health': 'Health check',
            'POST /api/chat': 'Chat với RAG system',
            'POST /api/search': 'Tìm kiếm semantic',
            'POST /api/intent': 'Phân loại intent',
            'GET /api/system-info': 'Thông tin hệ thống'
        },
        'example_requests': {
            'chat': {
                'url': '/api/chat',
                'method': 'POST',
                'body': {'message': 'Thành phần của Coca-Cola Original là gì?'}
            },
            'search': {
                'url': '/api/search',
                'method': 'POST',
                'body': {'query': 'thành phần Coca-Cola', 'k': 5}
            },
            'intent': {
                'url': '/api/intent',
                'method': 'POST',
                'body': {'message': 'Thành phần của Coca-Cola Original là gì?'}
            }
        }
    })

if __name__ == '__main__':
    # Khởi tạo hệ thống RAG
    if initialize_rag_system():
        logger.info("Khởi động Flask API...")
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        logger.error("Không thể khởi động API do lỗi khởi tạo RAG system") 