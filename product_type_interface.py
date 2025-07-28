import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import Dict, List

class ProductTypeInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Coca-Cola Product Type Selector")
        self.root.geometry("1200x800")
        
        # Product type mapping based on the image
        self.product_type_mapping = {
            "Nước ngọt có ga": "Các loại nước có gas, có vị ngọt, thường nhiều đường hoặc zero calorie",
            "Nước lọc / nước tinh khiết": "Nước uống không hương vị, không gas",
            "Nước tăng lực / Thức uống thể thao": "Có chứa điện giải, caffeine hoặc đường năng lượng cao",
            "Nước trái cây / trà": "Nước ép hoa quả, trà đóng chai, nước có vị tự nhiên",
            "Cà phê / Sữa / Đồ uống đặc biệt": "Các sản phẩm cà phê lon, sữa pha, đồ uống cao cấp",
            "Đồ uống có cồn (nếu có)": "Bia nhẹ, cocktail đóng lon hoặc các sản phẩm chứa cồn"
        }
        
        # Load products data
        self.products = self.load_products()
        
        # Current product index
        self.current_product_index = 0
        
        # Create interface
        self.create_widgets()
        
    def load_products(self):
        """Load products from JSON file"""
        # Try to load auto-classified products first
        try:
            with open('products_with_auto_types.json', 'r', encoding='utf-8') as f:
                products = json.load(f)
                print("Loaded auto-classified products from products_with_auto_types.json")
                return products
        except FileNotFoundError:
            # Fall back to original file
            try:
                with open('data/concatenated_products.json', 'r', encoding='utf-8') as f:
                    products = json.load(f)
                    print("Loaded original products from data/concatenated_products.json")
                    return products
            except FileNotFoundError:
                messagebox.showerror("Error", "Products file not found!")
                return []
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Invalid JSON file!")
                return []
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid auto-classified JSON file!")
            return []
    
    def create_widgets(self):
        """Create the main interface widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Coca-Cola Product Type Selector", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Product selection frame
        selection_frame = ttk.LabelFrame(main_frame, text="Product Selection", padding="10")
        selection_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        selection_frame.columnconfigure(1, weight=1)
        
        # Product name label and combobox
        ttk.Label(selection_frame, text="Product Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.product_var = tk.StringVar()
        self.product_combo = ttk.Combobox(selection_frame, textvariable=self.product_var, 
                                         state="readonly", width=50)
        self.product_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Populate product names
        product_names = [product.get('product_name', 'Unknown') for product in self.products if product.get('product_name')]
        self.product_combo['values'] = product_names
        if product_names:
            self.product_combo.set(product_names[0])
        
        # Product type selection frame
        type_frame = ttk.LabelFrame(main_frame, text="Product Type Assignment", padding="10")
        type_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        type_frame.columnconfigure(1, weight=1)
        
        # Product type label and combobox
        ttk.Label(type_frame, text="Product Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(type_frame, textvariable=self.type_var, 
                                      state="readonly", width=50)
        self.type_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Populate product types
        self.type_combo['values'] = list(self.product_type_mapping.keys())
        
        # Product type description
        ttk.Label(type_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.description_text = tk.Text(type_frame, height=3, width=50, wrap=tk.WORD, state=tk.DISABLED)
        self.description_text.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(10, 0))
        
        # Auto-classification info (if available)
        self.auto_info_label = ttk.Label(type_frame, text="", foreground="blue")
        self.auto_info_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        # Save button
        save_btn = ttk.Button(button_frame, text="Save Assignment", command=self.save_assignment)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Next button
        next_btn = ttk.Button(button_frame, text="Next Product", command=self.next_product)
        next_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Previous button
        prev_btn = ttk.Button(button_frame, text="Previous Product", command=self.previous_product)
        prev_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        clear_btn = ttk.Button(button_frame, text="Clear", command=self.clear_selection)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Export button
        export_btn = ttk.Button(button_frame, text="Export Data", command=self.export_data)
        export_btn.pack(side=tk.LEFT)
        
        # Progress label
        self.progress_label = ttk.Label(main_frame, text="")
        self.progress_label.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Assigned Products", padding="10")
        results_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Treeview for results
        columns = ('Product Name', 'Product Type', 'Description')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid treeview and scrollbar
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind events
        self.type_combo.bind('<<ComboboxSelected>>', self.update_description)
        self.product_combo.bind('<<ComboboxSelected>>', self.on_product_selected)
        
        # Store assignments
        self.assignments = {}
        
        # Update progress
        self.update_progress()
        
    def update_progress(self):
        """Update progress label"""
        total_products = len([p for p in self.products if p.get('product_name')])
        assigned_count = len(self.assignments)
        self.progress_label.config(text=f"Progress: {assigned_count}/{total_products} products assigned")
        
    def next_product(self):
        """Move to next product"""
        # First save current assignment if product type is selected
        current_product = self.product_var.get()
        current_type = self.type_var.get()
        
        if current_product and current_type:
            # Auto-save current assignment
            self.assignments[current_product] = {
                'product_name': current_product,
                'product_type': current_type,
                'product_type_description': self.product_type_mapping.get(current_type, '')
            }
            # Update treeview and progress
            self.update_treeview()
            self.update_progress()
        
        # Move to next product
        product_names = [product.get('product_name', 'Unknown') for product in self.products if product.get('product_name')]
        if not product_names:
            return
            
        self.current_product_index = (self.current_product_index + 1) % len(product_names)
        self.product_combo.set(product_names[self.current_product_index])
        self.on_product_selected()
        
    def previous_product(self):
        """Move to previous product"""
        # First save current assignment if product type is selected
        current_product = self.product_var.get()
        current_type = self.type_var.get()
        
        if current_product and current_type:
            # Auto-save current assignment
            self.assignments[current_product] = {
                'product_name': current_product,
                'product_type': current_type,
                'product_type_description': self.product_type_mapping.get(current_type, '')
            }
            # Update treeview and progress
            self.update_treeview()
            self.update_progress()
        
        # Move to previous product
        product_names = [product.get('product_name', 'Unknown') for product in self.products if product.get('product_name')]
        if not product_names:
            return
            
        self.current_product_index = (self.current_product_index - 1) % len(product_names)
        self.product_combo.set(product_names[self.current_product_index])
        self.on_product_selected()
        
    def update_description(self, event=None):
        """Update description when product type is selected"""
        selected_type = self.type_var.get()
        if selected_type in self.product_type_mapping:
            description = self.product_type_mapping[selected_type]
            self.description_text.config(state=tk.NORMAL)
            self.description_text.delete(1.0, tk.END)
            self.description_text.insert(1.0, description)
            self.description_text.config(state=tk.DISABLED)
    
    def on_product_selected(self, event=None):
        """Handle product selection"""
        selected_product = self.product_var.get()
        
        # Check if this product has auto-classification
        auto_classified = False
        for product in self.products:
            if product.get('product_name') == selected_product:
                if 'product_type' in product and product.get('product_type'):
                    auto_classified = True
                    # Set the auto-classified type
                    self.type_var.set(product.get('product_type'))
                    self.update_description()
                    
                    # Show auto-classification info
                    confidence = product.get('classification_confidence', '')
                    reasoning = product.get('classification_reasoning', '')
                    if confidence or reasoning:
                        info_text = f"Auto-classified (Confidence: {confidence})"
                        if reasoning:
                            info_text += f" - {reasoning[:100]}{'...' if len(reasoning) > 100 else ''}"
                        self.auto_info_label.config(text=info_text)
                    else:
                        self.auto_info_label.config(text="")
                    break
        
        if not auto_classified:
            # Check if user has manually assigned
            if selected_product in self.assignments:
                # Load existing assignment
                assigned_type = self.assignments[selected_product]['product_type']
                self.type_var.set(assigned_type)
                self.update_description()
            else:
                # Clear type selection for new product
                self.type_var.set('')
                self.description_text.config(state=tk.NORMAL)
                self.description_text.delete(1.0, tk.END)
                self.description_text.config(state=tk.DISABLED)
            
            # Clear auto-classification info
            self.auto_info_label.config(text="")
    
    def save_assignment(self):
        """Save the current product type assignment"""
        product_name = self.product_var.get()
        product_type = self.type_var.get()
        
        if not product_name:
            messagebox.showwarning("Warning", "Please select a product!")
            return
        
        if not product_type:
            messagebox.showwarning("Warning", "Please select a product type!")
            return
        
        # Save assignment
        self.assignments[product_name] = {
            'product_name': product_name,
            'product_type': product_type,
            'product_type_description': self.product_type_mapping.get(product_type, '')
        }
        
        # Update treeview
        self.update_treeview()
        
        # Update progress
        self.update_progress()
        
        messagebox.showinfo("Success", f"Product type assigned to {product_name}")
    
    def update_treeview(self):
        """Update the treeview with current assignments"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add assignments
        for product_name, assignment in self.assignments.items():
            self.tree.insert('', tk.END, values=(
                assignment['product_name'],
                assignment['product_type'],
                assignment['product_type_description']
            ))
    
    def clear_selection(self):
        """Clear current selection"""
        self.product_var.set('')
        self.type_var.set('')
        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        self.description_text.config(state=tk.DISABLED)
    
    def export_data(self):
        """Export assignments to JSON file"""
        if not self.assignments:
            messagebox.showwarning("Warning", "No assignments to export!")
            return
        
        try:
            # Create export data with full product information
            export_data = []
            for product_name, assignment in self.assignments.items():
                # Find the original product data
                product_data = None
                for product in self.products:
                    if product.get('product_name') == product_name:
                        product_data = product.copy()
                        break
                
                if product_data:
                    # Add the new fields
                    product_data['product_type'] = assignment['product_type']
                    product_data['product_type_description'] = assignment['product_type_description']
                    export_data.append(product_data)
            
            # Save to file
            with open('products_with_types.json', 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"Data exported to products_with_types.json\n{len(export_data)} products exported")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")

def main():
    root = tk.Tk()
    app = ProductTypeInterface(root)
    root.mainloop()

if __name__ == "__main__":
    main() 