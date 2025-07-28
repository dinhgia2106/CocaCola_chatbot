// popup.js
document.addEventListener('DOMContentLoaded', () => {
    const crawlBtn = document.getElementById('crawlBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const outputPre = document.getElementById('output');
    
    let scrapedData = null; 

    // Đặt hàm scrapeProductData ở đây hoặc trong một tệp riêng biệt
    // (Đặt ở ngoài vẫn hoạt động nhưng đây là thực hành tốt)
    function scrapeProductData() {
        // --- Ánh xạ các thuật ngữ (Mappings) ---
        const NUTRITION_MAP = {
            calories: ['NĂNG LƯỢNG'],
            protein: ['CHẤT ĐẠM'],
            total_fat: ['CHẤT BÉO'],
            total_carbohydrate: ['CARBOHYDRATE', 'CHẤT BỘT ĐƯỜNG'],
            sodium: ['NATRI'],
            total_sugars: ['ĐƯỜNG'],
        };
    
        const INGREDIENTS_HEADER_TEXT = ['Thành phần'];
        const AVAILABLE_SIZES_TEXT = 'Có các loại bao bì:';
    
        // --- Các hàm trợ giúp ---
        const getText = (element, selector) => {
            const child = element.querySelector(selector);
            return child ? child.innerText.trim() : "";
        };
    
        const getFullUrl = (relativeUrl) => {
            if (!relativeUrl) return "";
            try {
                if (relativeUrl.startsWith('http') || relativeUrl.startsWith('/')) {
                    return new URL(relativeUrl, window.location.origin).href;
                }
                return relativeUrl;
            } catch (e) {
                console.error("Lỗi URL không hợp lệ:", e);
                return "";
            }
        };
    
        // Hàm tìm một hàng dinh dưỡng, không phân biệt chữ hoa/thường
        const getNutritionRow = (container, possibleNames) => {
            const rows = container.querySelectorAll('.nutritional-information__row');
            for (const row of rows) {
                const labelEl = row.querySelector('.column1');
                if (labelEl) {
                    const labelText = labelEl.innerText.trim().toUpperCase();
                    if (possibleNames.some(name => labelText.includes(name.toUpperCase()))) {
                        return row;
                    }
                }
            }
            return null;
        };
    
        // Hàm phân tích giá trị dinh dưỡng, xử lý ký tự '≤' và dấu phẩy thập phân
        const parseNutritionValue = (row) => {
            if (!row) return null;
            const valEl = row.querySelector('.column3');
            if (!valEl) return null;
            const textValue = valEl.innerText.trim();
            // Loại bỏ ký tự không phải số ở đầu (như ≤), thay thế dấu phẩy bằng dấu chấm
            const cleanedValue = textValue.replace(/^[^0-9]+/, '').split(' ')[0].replace(',', '.').trim();
            return cleanedValue || null;
        };
    
    
        const allProductsData = [];
        const productElements = document.querySelectorAll('div.product-information');
    
        productElements.forEach(productEl => {
            const contentContainer = productEl.querySelector('.product-information__content') || productEl;
            if (!contentContainer) return;
    
            const productData = {
                "product_name": "",
                "description": "",
                "available_sizes": [],
                "nutrition_facts": {
                    "serving_size": "",
                    "servings_per_container": null,
                    "calories": null,
                    "total_fat": { "value": null, "daily_value": "" },
                    "sodium": { "value": null, "daily_value": "" },
                    "total_carbohydrate": { "value": null, "daily_value": "" },
                    "total_sugars": { "value": null, "includes_added_sugars": { "value": null, "daily_value": "" } },
                    "protein": { "value": null, "daily_value": "" }
                },
                "ingredients": [],
                "product_image_link": ""
            };
    
            // --- Thông tin cơ bản, Mô tả và Kích thước ---
            productData.product_name = getText(contentContainer, 'h3.cmp-title__text');
            
            const textElementsContainer = contentContainer.querySelector('.text:not(.footer__mobile-accordion)');
            if (textElementsContainer) {
                const allParagraphs = Array.from(textElementsContainer.querySelectorAll('p'));
                const descriptionParts = [];
    
                allParagraphs.forEach(p => {
                    const pText = p.innerText.trim();
                    // Kiểm tra và trích xuất kích thước
                    if (pText.includes(AVAILABLE_SIZES_TEXT)) {
                        const sizesText = pText.replace(new RegExp(AVAILABLE_SIZES_TEXT, 'i'), '').trim();
                        productData.available_sizes = sizesText.split(/,|,\s*|\n/).map(s => s.trim()).filter(Boolean);
                    } else {
                        // Nếu không phải là dòng kích thước, thêm vào mô tả
                        descriptionParts.push(pText);
                    }
                });
                productData.description = descriptionParts.join(' ').replace(/\s+/g, ' ');
            }
    
            const imgEl = productEl.querySelector('img.cmp-image__image');
            productData.product_image_link = imgEl ? getFullUrl(imgEl.getAttribute('src')) : '';
            
            // --- Dinh dưỡng & Thành phần ---
            const nutritionContainer = productEl.querySelector('.nutritional-information');
            if (nutritionContainer) {
                const nf = productData.nutrition_facts;
    
                const servingSizeRow = getNutritionRow(nutritionContainer, ['GIÁ TRỊ DINH DƯỠNG TRONG']);
                if (servingSizeRow) {
                    nf.serving_size = servingSizeRow.querySelector('.column3')?.innerText.trim() || "";
                }
    
                // Dùng parseFloat để xử lý số thập phân
                nf.calories = parseFloat(parseNutritionValue(getNutritionRow(nutritionContainer, NUTRITION_MAP.calories))) || null;
                nf.total_fat.value = parseNutritionValue(getNutritionRow(nutritionContainer, NUTRITION_MAP.total_fat));
                nf.sodium.value = parseNutritionValue(getNutritionRow(nutritionContainer, NUTRITION_MAP.sodium));
                nf.total_carbohydrate.value = parseNutritionValue(getNutritionRow(nutritionContainer, NUTRITION_MAP.total_carbohydrate));
                nf.protein.value = parseNutritionValue(getNutritionRow(nutritionContainer, NUTRITION_MAP.protein));
                nf.total_sugars.value = parseNutritionValue(getNutritionRow(nutritionContainer, NUTRITION_MAP.total_sugars));
    
                // Logic lấy thành phần đã được cải tiến
                const ingredientsHeaderEl = Array.from(nutritionContainer.querySelectorAll('h3')).find(h => 
                    INGREDIENTS_HEADER_TEXT.some(header => h.innerText.trim().includes(header))
                );
                if (ingredientsHeaderEl && ingredientsHeaderEl.nextElementSibling && ingredientsHeaderEl.nextElementSibling.tagName === 'P') {
                    let ingredientsText = ingredientsHeaderEl.nextElementSibling.innerText.trim();
                    ingredientsText = ingredientsText.replace(/\.$/, ''); // Xóa dấu chấm cuối dòng
                    productData.ingredients = ingredientsText.split(/,|、|–/).map(i => i.trim()).filter(Boolean);
                }
            }
            
            if (productData.product_name) {
                allProductsData.push(productData);
            }
        });
    
        return allProductsData;
    }

    crawlBtn.addEventListener('click', async () => {
        console.log("Crawl button clicked."); // LOG 1
        outputPre.textContent = 'Crawling...';
        downloadBtn.disabled = true;
        scrapedData = null;

        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            console.log("Active tab found:", tab); // LOG 2

            if (!tab) {
                outputPre.textContent = 'Error: Could not find active tab.';
                console.error("No active tab found.");
                return;
            }

            // Kiểm tra xem tab có URL hợp lệ không
            if (tab.url.startsWith('chrome://')) {
                 outputPre.textContent = 'Cannot run on internal Chrome pages.';
                 console.error("Attempting to run on a chrome:// page.");
                 return;
            }

            console.log("Executing script on tab ID:", tab.id); // LOG 3
            chrome.scripting.executeScript({
                target: { tabId: tab.id },
                function: scrapeProductData, 
            }, (injectionResults) => {
                console.log("executeScript callback fired."); // LOG 4
                
                // lastError thường là nơi báo lỗi quyền
                if (chrome.runtime.lastError) {
                    outputPre.textContent = 'Error: ' + chrome.runtime.lastError.message;
                    console.error("Chrome runtime error:", chrome.runtime.lastError); // LOG 5
                    return;
                }

                console.log("Injection results:", injectionResults); // LOG 6
                if (injectionResults && injectionResults[0] && injectionResults[0].result) {
                    scrapedData = injectionResults[0].result;
                    if (scrapedData.length === 0) {
                         outputPre.textContent = 'No products found on this page with a recognizable structure.';
                    } else {
                        outputPre.textContent = JSON.stringify(scrapedData, null, 2);
                        downloadBtn.disabled = false;
                    }
                } else {
                    outputPre.textContent = 'Could not retrieve data. Ensure you are on a valid product page and the extension has permissions.';
                }
            });

        } catch (error) {
            outputPre.textContent = 'An unexpected error occurred: ' + error.message;
            console.error("Error in crawlBtn click listener:", error);
        }
    });

    downloadBtn.addEventListener('click', () => {
        if (!scrapedData) {
            outputPre.textContent = 'No data to download. Please crawl a page first.';
            return;
        }

        const dataStr = JSON.stringify(scrapedData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = 'coca-cola-products.json';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        outputPre.textContent = 'Download completed!';
    });
});