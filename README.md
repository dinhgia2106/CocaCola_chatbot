# Coca-Cola RAG System

Hệ thống RAG (Retrieval-Augmented Generation) hoàn chỉnh cho Coca-Cola chatbot với vector database và intent classification.

## Tính năng chính

### 3 Cấp độ Chunking
1. **Cấp 1 - Chunk Chi Tiết**: Tập trung vào từng thuộc tính cụ thể
2. **Cấp 2 - Chunk Tổng Hợp**: Thông tin toàn diện về một sản phẩm
3. **Cấp 3 - Chunk Tổng Quan**: Nhóm sản phẩm theo đặc tính

### Vector Database với FAISS
- Sử dụng `paraphrase-multilingual-MiniLM-L12-v2` để tạo embeddings
- Hỗ trợ 3 loại FAISS index:
  - `IndexFlatL2`: Tìm kiếm chính xác nhất, chậm nhất
  - `IndexIVFFlat`: Cân bằng tốc độ và độ chính xác
  - `IndexIVFPQ`: Nhanh nhất, tiết kiệm bộ nhớ

### Intent Classification
- Sử dụng Gemini API để phân loại ý định người dùng
- Hỗ trợ 14 loại intent khác nhau
- Xoay vòng 3 API keys khi có lỗi

### Flask API
- RESTful API với 5 endpoints chính
- Hỗ trợ CORS
- Health check và system info

## Cài đặt

1. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

2. Cấu hình API keys:
   - Copy file `env_example.txt` thành `.env`
   - Thêm các Gemini API keys vào file `.env`

## Sử dụng

### 1. Tạo chunks và vector database:
```bash
# Tạo chunks
python chunking_system.py

# Tạo vector database
python vector_database.py
```

### 2. Chạy demo:
```bash
python demo_rag.py
```

### 3. Khởi động Flask API:
```bash
python app.py
```

### 4. Sử dụng trong code:
```python
from rag_system import RAGSystem

# Khởi tạo hệ thống
rag_system = RAGSystem()

# Gửi câu hỏi
result = rag_system.generate_response("Thành phần của Coca-Cola Original là gì?")
print(result['response'])
```

## API Endpoints

### 1. Chat API
```bash
POST /api/chat
Content-Type: application/json

{
    "message": "Thành phần của Coca-Cola Original là gì?"
}
```

### 2. Search API
```bash
POST /api/search
Content-Type: application/json

{
    "query": "thành phần Coca-Cola",
    "k": 5
}
```

### 3. Intent Classification API
```bash
POST /api/intent
Content-Type: application/json

{
    "message": "Thành phần của Coca-Cola Original là gì?"
}
```

### 4. System Info API
```bash
GET /api/system-info
```

### 5. Health Check API
```bash
GET /health
```

## Cấu trúc dự án

```
CocaCola_chatbot/
├── data/
│   └── final_product_data.json      # Dữ liệu sản phẩm
├── chunks/                          # Thư mục chứa chunks
│   ├── level_1_chunks.json
│   ├── level_2_chunks.json
│   ├── level_3_chunks.json
│   └── all_chunks.json
├── vector_db/                       # Thư mục chứa vector database
│   ├── coca_cola_index.index
│   └── coca_cola_index.metadata
├── chunking_system.py               # Hệ thống tạo chunks
├── intent_classifier.py             # Phân loại intent
├── vector_database.py               # Vector database với FAISS
├── rag_system.py                    # Hệ thống RAG chính
├── demo_rag.py                      # Demo hệ thống
├── app.py                          # Flask API
├── requirements.txt                 # Dependencies
└── README.md                       # Hướng dẫn này
```

## Ví dụ sử dụng API

### Chat với RAG system:
```python
import requests

response = requests.post('http://localhost:5000/api/chat', json={
    'message': 'Thành phần của Coca-Cola Original là gì?'
})

result = response.json()
print(result['response'])
```

### Tìm kiếm semantic:
```python
response = requests.post('http://localhost:5000/api/search', json={
    'query': 'thành phần Coca-Cola',
    'k': 5
})

results = response.json()['results']
for result in results:
    print(f"Score: {result['score']:.4f}")
    print(f"Content: {result['content'][:100]}...")
```

### Phân loại intent:
```python
response = requests.post('http://localhost:5000/api/intent', json={
    'message': 'Thành phần của Coca-Cola Original là gì?'
})

result = response.json()
print(f"Intent: {result['intent']}")
print(f"Entities: {result['entities']}")
```

## Cấu hình FAISS Index

### IndexFlatL2 (Mặc định):
```python
from vector_database import create_vector_database

# Tạo index chính xác nhất
vdb = create_vector_database(index_type="IndexFlatL2")
```

### IndexIVFFlat:
```python
# Tạo index cân bằng tốc độ và độ chính xác
vdb = create_vector_database(index_type="IndexIVFFlat")
```

### IndexIVFPQ:
```python
# Tạo index nhanh nhất, tiết kiệm bộ nhớ
vdb = create_vector_database(index_type="IndexIVFPQ")
```

## Lưu ý

- Hệ thống sử dụng Gemini API để phân loại intent
- Cần cấu hình API keys trong file `.env`
- Chunks và vector database được tạo tự động
- Hỗ trợ xoay vòng API keys khi có lỗi
- FAISS index được lưu và load tự động
- Flask API chạy trên port 5000 mặc định 