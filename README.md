# Coca-Cola Product RAG Chatbot

A retrieval-augmented chatbot that answers questions about Coca-Cola products — ingredients, nutrition, caffeine, sizes, comparisons and product ranges — in Vietnamese or English.

Its main idea: **classify the question first, then retrieve from the chunk level that fits it.** Fact lookups hit fine-grained chunks, product questions hit per-product summaries, and listing questions hit category overviews.

## How it works

```
question ─► intent classifier (Gemini) ─► intent + entities ─► chunk level 1 / 2 / 3
                                                                       │
                     FAISS search (multilingual MiniLM embeddings) ◄───┘
                                                                       │
                     Gemini 1.5 Flash answer generation ◄──────────────┘
```

### Three chunk levels

| Level | Content | Used for intents |
|---|---|---|
| 1 — detail | one attribute of one product | `get_ingredients`, `get_nutrition_facts`, `get_calories`, `get_sugar_content`, `check_caffeine`, `get_available_sizes` |
| 2 — product | everything about one product | `get_product_summary`, `compare_two_products`, `product_inquiry` |
| 3 — overview | products grouped by type, attribute or country | `list_by_product_type`, `list_by_attribute`, `list_by_country`, `explain_category` |

### Retrieval

- Embeddings: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- FAISS index type is configurable: `IndexFlatL2` (exact, default), `IndexIVFFlat` (balanced) or `IndexIVFPQ` (fastest, smallest)

### Data collection

`Crawl_extension/` is a small Chrome extension that scrapes product pages from the Coca-Cola website into JSON (`data/final_product_data.json`, plus FAQ and product files).

### Reliability

Up to three Gemini API keys are rotated automatically when a request fails or hits a rate limit.

## Running

```bash
pip install -r requirements.txt

# .env  (see .env.example)
GEMINI_API_KEY_1=...
GEMINI_API_KEY_2=...
GEMINI_API_KEY_3=...

python chunking_system.py   # build chunks/level_{1,2,3}_chunks.json
python vector_database.py   # build vector_db/coca_cola_index.*
python demo_rag.py          # console demo
python app.py               # Flask API on http://localhost:5000
```

Prebuilt chunks and the FAISS index are included, so `app.py` can run directly. `Procfile` and `render.yaml` are provided for deployment on Render.

```python
from rag_system import RAGSystem

rag = RAGSystem()
print(rag.generate_response("Thành phần của Coca-Cola Original là gì?")["response"])
```

## API

| Method | Endpoint | Body | Returns |
|---|---|---|---|
| `POST` | `/api/chat` | `{"message": "..."}` | generated answer |
| `POST` | `/api/search` | `{"query": "...", "k": 5}` | top-k chunks with scores |
| `POST` | `/api/intent` | `{"message": "..."}` | intent and extracted entities |
| `GET` | `/api/system-info` | | index and model information |
| `GET` | `/health` | | health check |

```python
import requests
r = requests.post("http://localhost:5000/api/search", json={"query": "Coca-Cola ingredients", "k": 5})
for hit in r.json()["results"]:
    print(f"{hit['score']:.4f}  {hit['content'][:100]}")
```

## Repository

```
chunking_system.py   builds the three chunk levels
vector_database.py   embeddings + FAISS index (create_vector_database(index_type=...))
intent_classifier.py Gemini intent and entity extraction
llm_generator.py     answer generation with key rotation
rag_system.py        end-to-end RAG pipeline
app.py               Flask API (CORS enabled)
demo_rag.py          console demo
test_api.ipynb       API smoke tests
data/ chunks/ vector_db/
Crawl_extension/     product scraper
```
