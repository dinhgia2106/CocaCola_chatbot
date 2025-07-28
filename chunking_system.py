import json
import os
from typing import List, Dict, Any
from collections import defaultdict
import re

class CocaColaChunkingSystem:
    def __init__(self, data_file_path: str):
        self.data_file_path = data_file_path
        self.products = self.load_data()
        
    def load_data(self) -> List[Dict]:
        with open(self.data_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def create_level_1_chunks(self) -> List[Dict]:
        """Tạo chunk cấp 1 - Chi tiết từng thuộc tính"""
        chunks = []
        
        for product in self.products:
            product_name = product.get('product_name', '')
            country = product.get('country', '')
            
            # Chunk thành phần
            if 'ingredients' in product:
                chunk = {
                    "content": f"Thông tin thành phần của sản phẩm {product_name} tại {country}:\n" + 
                              "\n".join([f"- {ingredient}" for ingredient in product['ingredients']]),
                    "metadata": {
                        "product_name": product_name,
                        "country": country,
                        "chunk_level": 1,
                        "attribute": "ingredients"
                    }
                }
                chunks.append(chunk)
            
            # Chunk dinh dưỡng
            if 'nutrition_facts' in product:
                nutrition = product['nutrition_facts']
                serving_size = nutrition.get('serving_size', '')
                calories = nutrition.get('calories', '')
                
                nutrition_text = f"Thông tin dinh dưỡng của sản phẩm {product_name} tại {country} (khẩu phần {serving_size}):\n"
                
                if calories:
                    nutrition_text += f"- Calo: {calories}\n"
                
                for key, value in nutrition.items():
                    if key not in ['calories', 'serving_size', 'servings_per_container']:
                        if isinstance(value, dict):
                            if 'value' in value:
                                nutrition_text += f"- {key.replace('_', ' ').title()}: {value['value']}"
                                if 'daily_value' in value and value['daily_value'] != '-':
                                    nutrition_text += f" ({value['daily_value']} DV)"
                                nutrition_text += "\n"
                        else:
                            nutrition_text += f"- {key.replace('_', ' ').title()}: {value}\n"
                
                chunk = {
                    "content": nutrition_text,
                    "metadata": {
                        "product_name": product_name,
                        "country": country,
                        "chunk_level": 1,
                        "attribute": "nutrition_facts"
                    }
                }
                chunks.append(chunk)
            
            # Chunk mô tả
            if 'description' in product:
                chunk = {
                    "content": f"Mô tả sản phẩm {product_name} tại {country}: {product['description']}",
                    "metadata": {
                        "product_name": product_name,
                        "country": country,
                        "chunk_level": 1,
                        "attribute": "description"
                    }
                }
                chunks.append(chunk)
            
            # Chunk kích cỡ có sẵn
            if 'available_sizes' in product:
                chunk = {
                    "content": f"Các kích cỡ có sẵn của sản phẩm {product_name} tại {country}:\n" + 
                              "\n".join([f"- {size}" for size in product['available_sizes']]),
                    "metadata": {
                        "product_name": product_name,
                        "country": country,
                        "chunk_level": 1,
                        "attribute": "available_sizes"
                    }
                }
                chunks.append(chunk)
        
        return chunks
    
    def create_level_2_chunks(self) -> List[Dict]:
        """Tạo chunk cấp 2 - Tổng hợp sản phẩm"""
        chunks = []
        
        for product in self.products:
            product_name = product.get('product_name', '')
            country = product.get('country', '')
            
            # Tạo nội dung tổng hợp
            content = f"Tên sản phẩm: {product_name}\n"
            content += f"Quốc gia: {country}\n"
            
            if 'description' in product:
                content += f"Mô tả: {product['description']}\n"
            
            if 'available_sizes' in product:
                content += f"Các kích cỡ có sẵn: {', '.join(product['available_sizes'])}\n"
            
            if 'ingredients' in product:
                content += f"Thành phần: {', '.join(product['ingredients'])}\n"
            
            if 'nutrition_facts' in product:
                nutrition = product['nutrition_facts']
                serving_size = nutrition.get('serving_size', '')
                content += f"Thông tin dinh dưỡng (cho mỗi {serving_size}):\n"
                
                calories = nutrition.get('calories', '')
                if calories:
                    content += f"Calo: {calories}\n"
                
                for key, value in nutrition.items():
                    if key not in ['calories', 'serving_size', 'servings_per_container']:
                        if isinstance(value, dict):
                            if 'value' in value:
                                content += f"{key.replace('_', ' ').title()}: {value['value']}"
                                if 'daily_value' in value and value['daily_value'] != '-':
                                    content += f" ({value['daily_value']} DV)"
                                content += "\n"
                        else:
                            content += f"{key.replace('_', ' ').title()}: {value}\n"
            
            chunk = {
                "content": content,
                "metadata": {
                    "product_name": product_name,
                    "country": country,
                    "chunk_level": 2
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def create_level_3_chunks(self) -> List[Dict]:
        """Tạo chunk cấp 3 - Tổng quan theo nhóm"""
        chunks = []
        
        # Nhóm theo quốc gia
        country_groups = defaultdict(list)
        for product in self.products:
            country = product.get('country', 'unknown')
            country_groups[country].append(product)
        
        for country, products in country_groups.items():
            content = f"Danh sách các sản phẩm có sẵn tại {country}:\n"
            for product in products:
                content += f"- {product.get('product_name', 'Unknown')}\n"
            
            chunk = {
                "content": content,
                "metadata": {
                    "summary_type": "country_list",
                    "country": country,
                    "chunk_level": 3
                }
            }
            chunks.append(chunk)
        
        # Nhóm theo đặc tính không đường
        zero_sugar_products = []
        regular_products = []
        
        for product in self.products:
            product_name = product.get('product_name', '').lower()
            if any(keyword in product_name for keyword in ['zero', 'diet', 'light']):
                zero_sugar_products.append(product)
            else:
                regular_products.append(product)
        
        if zero_sugar_products:
            content = "Danh sách các sản phẩm không đường (Zero Sugar) có sẵn bao gồm:\n"
            for product in zero_sugar_products:
                content += f"- {product.get('product_name', 'Unknown')}\n"
            content += "\nNhững sản phẩm này thường sử dụng chất tạo ngọt thay thế đường để cung cấp vị ngọt mà không có hoặc có rất ít calo."
            
            chunk = {
                "content": content,
                "metadata": {
                    "summary_type": "attribute_list",
                    "attribute": "zero_sugar",
                    "chunk_level": 3
                }
            }
            chunks.append(chunk)
        
        # Nhóm theo loại sản phẩm (dựa trên tên)
        product_types = defaultdict(list)
        for product in self.products:
            product_name = product.get('product_name', '').lower()
            
            if 'coca-cola' in product_name or 'coke' in product_name:
                product_types['Coca-Cola'].append(product)
            elif 'fanta' in product_name:
                product_types['Fanta'].append(product)
            elif 'sprite' in product_name:
                product_types['Sprite'].append(product)
            elif 'dasani' in product_name:
                product_types['Dasani'].append(product)
            elif 'vitaminwater' in product_name:
                product_types['Vitaminwater'].append(product)
            else:
                product_types['Other'].append(product)
        
        for product_type, products in product_types.items():
            if products:
                content = f"Danh sách các sản phẩm thuộc loại '{product_type}' bao gồm:\n"
                for product in products:
                    content += f"- {product.get('product_name', 'Unknown')}\n"
                
                chunk = {
                    "content": content,
                    "metadata": {
                        "summary_type": "product_type_list",
                        "product_type": product_type,
                        "chunk_level": 3
                    }
                }
                chunks.append(chunk)
        
        return chunks
    
    def create_all_chunks(self) -> Dict[str, List[Dict]]:
        """Tạo tất cả các chunk theo 3 cấp độ"""
        return {
            "level_1_chunks": self.create_level_1_chunks(),
            "level_2_chunks": self.create_level_2_chunks(),
            "level_3_chunks": self.create_level_3_chunks()
        }
    
    def save_chunks(self, output_dir: str = "chunks"):
        """Lưu các chunk vào file"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        all_chunks = self.create_all_chunks()
        
        for level, chunks in all_chunks.items():
            filename = f"{output_dir}/{level}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
            print(f"Đã lưu {len(chunks)} chunks vào {filename}")
        
        # Lưu tất cả chunks vào một file
        all_chunks_combined = []
        for level, chunks in all_chunks.items():
            all_chunks_combined.extend(chunks)
        
        with open(f"{output_dir}/all_chunks.json", 'w', encoding='utf-8') as f:
            json.dump(all_chunks_combined, f, ensure_ascii=False, indent=2)
        print(f"Đã lưu tổng cộng {len(all_chunks_combined)} chunks vào {output_dir}/all_chunks.json")

def main():
    chunking_system = CocaColaChunkingSystem("data/final_product_data.json")
    chunking_system.save_chunks()
    
    # In thống kê
    all_chunks = chunking_system.create_all_chunks()
    print("\nThống kê chunks:")
    for level, chunks in all_chunks.items():
        print(f"{level}: {len(chunks)} chunks")

if __name__ == "__main__":
    main()