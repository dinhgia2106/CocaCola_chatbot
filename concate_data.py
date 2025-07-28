import json
import re
import os

def extract_country_from_image_link(image_link):
    """Extract country code from product_image_link"""
    if not image_link:
        return "unknown"
    
    # Pattern to match country code after 'onexp/'
    pattern = r'onexp/([a-z]{2})/'
    match = re.search(pattern, image_link)
    
    if match:
        return match.group(1)
    else:
        return "unknown"

def concate_data_files():
    """Concate all data files from 1.json to 41.json and add country field"""
    all_products = []
    
    # Process files from 1 to 41
    for i in range(1, 42):
        filename = f"data/{i}.json"
        
        if not os.path.exists(filename):
            print(f"File {filename} not found, skipping...")
            continue
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Add country field to each product
            for product in data:
                if isinstance(product, dict) and 'product_image_link' in product:
                    product['country'] = extract_country_from_image_link(product['product_image_link'])
                else:
                    product['country'] = "unknown"
                    
            all_products.extend(data)
            print(f"Processed {filename}: {len(data)} products")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    # Save concatenated data
    output_file = "data/concatenated_products.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)
    
    print(f"\nTotal products processed: {len(all_products)}")
    print(f"Concatenated data saved to: {output_file}")
    
    # Show country distribution
    country_counts = {}
    for product in all_products:
        country = product.get('country', 'unknown')
        country_counts[country] = country_counts.get(country, 0) + 1
    
    print("\nCountry distribution:")
    for country, count in sorted(country_counts.items()):
        print(f"  {country}: {count} products")

if __name__ == "__main__":
    concate_data_files() 