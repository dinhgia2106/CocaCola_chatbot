import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import pickle

class VectorDatabase:
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Khởi tạo vector database với model embedding và FAISS index
        
        Args:
            model_name: Tên model embedding từ sentence-transformers
        """
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks = []
        self.chunk_metadata = []
        
    def load_chunks(self, chunks_file: str = "chunks/all_chunks.json"):
        """Load chunks từ file JSON"""
        if not os.path.exists(chunks_file):
            raise FileNotFoundError(f"Không tìm thấy file {chunks_file}")
        
        with open(chunks_file, 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)
        
        self.chunk_metadata = [chunk.get('metadata', {}) for chunk in self.chunks]
        print(f"Đã load {len(self.chunks)} chunks")
        
    def create_embeddings(self) -> np.ndarray:
        """Tạo embeddings cho tất cả chunks"""
        if not self.chunks:
            raise ValueError("Chưa có chunks để tạo embeddings")
        
        # Trích xuất nội dung chunks
        contents = [chunk['content'] for chunk in self.chunks]
        
        # Tạo embeddings
        print("Đang tạo embeddings...")
        embeddings = self.model.encode(contents, show_progress_bar=True)
        
        print(f"Đã tạo embeddings với shape: {embeddings.shape}")
        return embeddings
    
    def build_index(self, embeddings: np.ndarray, index_type: str = "IndexFlatL2", 
                   nlist: int = 100, m: int = 8, bits: int = 8):
        """
        Xây dựng FAISS index
        
        Args:
            embeddings: Ma trận embeddings
            index_type: Loại index ("IndexFlatL2", "IndexIVFFlat", "IndexIVFPQ")
            nlist: Số cluster cho IVF (chỉ dùng cho IVF)
            m: Số sub-vectors cho PQ (chỉ dùng cho IndexIVFPQ)
            bits: Số bits cho PQ (chỉ dùng cho IndexIVFPQ)
        """
        dimension = embeddings.shape[1]
        
        if index_type == "IndexFlatL2":
            self.index = faiss.IndexFlatL2(dimension)
            print("Đã tạo IndexFlatL2")
            
        elif index_type == "IndexIVFFlat":
            # Tạo quantizer
            quantizer = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            print(f"Đã tạo IndexIVFFlat với {nlist} clusters")
            
        elif index_type == "IndexIVFPQ":
            # Tạo quantizer
            quantizer = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIVFPQ(quantizer, dimension, nlist, m, bits)
            print(f"Đã tạo IndexIVFPQ với {nlist} clusters, {m} sub-vectors, {bits} bits")
            
        else:
            raise ValueError(f"Không hỗ trợ index type: {index_type}")
        
        # Thêm vectors vào index
        if index_type in ["IndexIVFFlat", "IndexIVFPQ"]:
            # Cần train cho IVF
            print("Đang train index...")
            self.index.train(embeddings)
        
        print("Đang thêm vectors vào index...")
        self.index.add(embeddings)
        print(f"Đã thêm {self.index.ntotal} vectors vào index")
    
    def search(self, query: str, k: int = 5, metadata_filter: Dict = None) -> List[Dict]:
        if self.index is None:
            raise ValueError("Chưa có index, cần build index trước")
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        if not metadata_filter:
            scores, indices = self.index.search(query_embedding, k)
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx != -1:
                    results.append({'rank': i + 1, 'score': float(score), 'chunk': self.chunks[idx], 'index': int(idx)})
            return results
        # Nếu có filter, search top 100 rồi lọc
        search_k = min(self.index.ntotal, 100)
        scores, indices = self.index.search(query_embedding, search_k)
        filtered_results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            chunk_metadata = self.chunk_metadata[idx]
            is_match = True
            for key, value in metadata_filter.items():
                if chunk_metadata.get(key) != value:
                    is_match = False
                    break
            if is_match:
                filtered_results.append({'score': float(score), 'chunk': self.chunks[idx], 'index': int(idx)})
            if len(filtered_results) >= k:
                break
        return filtered_results
    
    def save_index(self, filepath: str):
        """Lưu index và metadata"""
        if self.index is None:
            raise ValueError("Chưa có index để lưu")
        
        # Lưu index
        faiss.write_index(self.index, f"{filepath}.index")
        
        # Lưu metadata
        metadata = {
            'chunks': self.chunks,
            'chunk_metadata': self.chunk_metadata
        }
        with open(f"{filepath}.metadata", 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"Đã lưu index và metadata vào {filepath}")
    
    def load_index(self, filepath: str):
        """Load index và metadata"""
        # Load index
        self.index = faiss.read_index(f"{filepath}.index")
        
        # Load metadata
        with open(f"{filepath}.metadata", 'rb') as f:
            metadata = pickle.load(f)
            self.chunks = metadata['chunks']
            self.chunk_metadata = metadata.get('chunk_metadata', [])
        
        print(f"Đã load index và metadata từ {filepath}")
        print(f"Index có {self.index.ntotal} vectors")

def create_vector_database(chunks_file: str = "chunks/all_chunks.json", 
                          index_type: str = "IndexFlatL2",
                          save_path: str = "vector_db/coca_cola_index"):
    """
    Tạo và lưu vector database
    
    Args:
        chunks_file: Đường dẫn file chunks
        index_type: Loại FAISS index
        save_path: Đường dẫn lưu index
    """
    # Tạo thư mục lưu
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # Khởi tạo vector database
    vdb = VectorDatabase()
    
    # Load chunks
    vdb.load_chunks(chunks_file)
    
    # Tạo embeddings
    embeddings = vdb.create_embeddings()
    
    # Build index
    if index_type == "IndexIVFFlat":
        vdb.build_index(embeddings, index_type, nlist=100)
    elif index_type == "IndexIVFPQ":
        vdb.build_index(embeddings, index_type, nlist=100, m=8, bits=8)
    else:
        vdb.build_index(embeddings, index_type)
    
    # Lưu index
    vdb.save_index(save_path)
    
    return vdb

if __name__ == "__main__":
    # Test tạo vector database
    print("Tạo vector database với IndexFlatL2...")
    vdb = create_vector_database(index_type="IndexFlatL2")
    
    # Test tìm kiếm
    print("\nTest tìm kiếm:")
    results = vdb.search("thành phần Coca-Cola", k=3)
    for result in results:
        print(f"Rank {result['rank']}: Score {result['score']:.4f}")
        print(f"Content: {result['chunk']['content'][:100]}...")
        print(f"Metadata: {result['chunk']['metadata']}")
        print("-" * 50) 