// popup.js
document.addEventListener('DOMContentLoaded', () => {
    const crawlBtn = document.getElementById('crawlBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const outputPre = document.getElementById('output');
    
    let scrapedData = null; // Biến lưu trữ dữ liệu đã crawl

    crawlBtn.addEventListener('click', async () => {
        outputPre.textContent = 'Crawling...';
        downloadBtn.disabled = true;
        scrapedData = null;

        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            function: scrapeProductData, // Hàm crawl đã được nâng cấp
        }, (injectionResults) => {
            if (chrome.runtime.lastError) {
                outputPre.textContent = 'Error: ' + chrome.runtime.lastError.message;
                return;
            }
            if (injectionResults && injectionResults[0] && injectionResults[0].result) {
                scrapedData = injectionResults[0].result;
                if (scrapedData.length === 0) {
                     outputPre.textContent = 'No products found on this page with a recognizable structure.';
                } else {
                    outputPre.textContent = JSON.stringify(scrapedData, null, 2);
                    downloadBtn.disabled = false; // Bật nút download khi có dữ liệu
                }
            } else {
                outputPre.textContent = 'Could not retrieve data. Make sure you are on a valid product page.';
            }
        });
    });

    downloadBtn.addEventListener('click', () => {
        if (!scrapedData) {
            alert('No data to download. Please crawl first.');
            return;
        }

        const dataStr = JSON.stringify(scrapedData, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = 'coca-cola-products.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });
});


function scrapeProductData() {
    // --- Multi-language Mappings ---
    const NUTRITION_MAP = {
        calories: ['エネルギー', 'Calories'],
        protein: ['たんぱく質', 'Protein'],
        total_fat: ['脂質', 'Total Fat'],
        total_carbohydrate: ['炭水化物', 'Total Carbohydrate'],
        sodium: ['食塩相当量', 'Sodium'], //食塩相当量 = salt equivalent
        total_sugars: ['Total Sugars'],
        includes_added_sugars: ['Includes Added Sugars'],
    };

    const INGREDIENTS_HEADER_TEXT = ['原材料名', 'Ingredients'];

    // --- Helper Functions ---
    const getText = (element, selector) => {
        const child = element.querySelector(selector);
        return child ? child.innerText.trim() : "";
    };

    const getFullUrl = (relativeUrl) => {
        if (!relativeUrl) return "";
        try {
            return new URL(relativeUrl, window.location.origin).href;
        } catch (e) { return ""; }
    };
    
    // Hàm tìm một hàng dinh dưỡng dựa trên danh sách các tên có thể có
    const getNutritionRow = (container, possibleNames) => {
        const rows = container.querySelectorAll('.nutritional-information__row');
        for (const row of rows) {
            const labelEl = row.querySelector('.column1');
            if (labelEl) {
                const labelText = labelEl.innerText.trim();
                if (possibleNames.some(name => labelText.includes(name))) {
                    return row;
                }
            }
        }
        return null;
    };
    
    const parseNutritionValue = (row) => {
        if (!row) return null;
        const valEl = row.querySelector('.column2, .column3');
        if (!valEl) return null;
        return valEl.innerText.split('（')[0].trim();
    };

    const parseDailyValue = (row) => {
        if (!row) return "";
        const dvEl = row.querySelector('.column3');
        return (dvEl && dvEl.innerText.includes('%')) ? dvEl.innerText.trim() : "";
    };

    const allProductsData = [];
    const productElements = document.querySelectorAll('div.product-information');

    productElements.forEach(productEl => {
        const contentContainer = productEl.querySelector('.product-information__content');
        if (!contentContainer) {
            return;
        }

        const productData = {
            "product_name": "", "description": "", "available_sizes": [],
            "nutrition_facts": {
                "serving_size": "", "servings_per_container": null, "calories": null,
                "total_fat": { "value": null, "daily_value": "" },
                "sodium": { "value": null, "daily_value": "" },
                "total_carbohydrate": { "value": null, "daily_value": "" },
                "total_sugars": { "value": null, "includes_added_sugars": { "value": null, "daily_value": "" } },
                "protein": { "value": null, "daily_value": "" }
            },
            "ingredients": [], "product_image_link": ""
        };

        // --- Basic Info ---
        productData.product_name = getText(contentContainer, 'h3.cmp-title__text');
        const descriptionEl = contentContainer.querySelector('.cmp-text');
        if (descriptionEl) {
            // Gom tất cả text trong các thẻ p, thay thế <br> bằng khoảng trắng
            let tempDiv = document.createElement('div');
            tempDiv.innerHTML = descriptionEl.innerHTML.replace(/<br\s*\/?>/gi, ' ');
            productData.description = tempDiv.innerText.trim().replace(/\s+/g, ' ');
        }
        
        const sizesEl = Array.from(contentContainer.querySelectorAll('.cmp-text p b')).find(b => b.innerText.toLowerCase().includes('available sizes'));
        if (sizesEl) {
            const sizesText = sizesEl.parentElement.innerText.replace(/Available Sizes:/i, '').trim();
            productData.available_sizes = sizesText.split(',').map(s => s.trim()).filter(Boolean);
        }

        const imgEl = productEl.querySelector('.adaptiveImage img.cmp-image__image');
        productData.product_image_link = imgEl ? getFullUrl(imgEl.getAttribute('src')) : '';
        
        // --- Nutrition & Ingredients (REVISED LOGIC) ---
        const nutritionContainer = productEl.querySelector('.nutritional-information');
        if (nutritionContainer) {
            const nf = productData.nutrition_facts;

            // Lấy Serving Size
            const allRows = nutritionContainer.querySelectorAll('.nutritional-information__row');
            // Tìm hàng đầu tiên sau hàng header có chứa text đặc trưng của serving size
            let servingSizeRowFound = false;
            for (const row of allRows) {
                const text = row.innerText.trim();
                if (text.includes('当たり') || text.includes('per container') || text.includes('Serving Size')) {
                    if (text.includes('当たり')) { // JP: 100ml当たり
                        nf.serving_size = text;
                    } else if (text.includes('Serving Size')) { // US: Serving Size ... 1 Bottle
                        nf.serving_size = row.querySelector('.column3')?.innerText.trim() || text;
                    } else if (text.includes('per container')) { // US: 1 serving per container
                         const match = text.match(/(\d+)/);
                         if(match) nf.servings_per_container = parseInt(match[1], 10);
                    }
                    servingSizeRowFound = true;
                }
            }

            // Lấy các giá trị dinh dưỡng dựa trên map
            nf.calories = parseInt(parseNutritionValue(getNutritionRow(nutritionContainer, NUTRITION_MAP.calories)), 10) || null;
            
            const fatRow = getNutritionRow(nutritionContainer, NUTRITION_MAP.total_fat);
            if(fatRow) { nf.total_fat.value = parseNutritionValue(fatRow); nf.total_fat.daily_value = parseDailyValue(fatRow); }
            
            const sodiumRow = getNutritionRow(nutritionContainer, NUTRITION_MAP.sodium);
            if(sodiumRow) { nf.sodium.value = parseNutritionValue(sodiumRow); nf.sodium.daily_value = parseDailyValue(sodiumRow); }
            
            const carbRow = getNutritionRow(nutritionContainer, NUTRITION_MAP.total_carbohydrate);
            if(carbRow) { nf.total_carbohydrate.value = parseNutritionValue(carbRow); nf.total_carbohydrate.daily_value = parseDailyValue(carbRow); }

            const proteinRow = getNutritionRow(nutritionContainer, NUTRITION_MAP.protein);
            if(proteinRow) { nf.protein.value = parseNutritionValue(proteinRow); nf.protein.daily_value = parseDailyValue(proteinRow); }

            // Chỉ lấy các trường này nếu tồn tại
            const sugarRow = getNutritionRow(nutritionContainer, NUTRITION_MAP.total_sugars);
            if(sugarRow) { nf.total_sugars.value = parseNutritionValue(sugarRow); }
            
            const addedSugarRow = getNutritionRow(nutritionContainer, NUTRITION_MAP.includes_added_sugars);
            if(addedSugarRow) { nf.total_sugars.includes_added_sugars.value = parseNutritionValue(addedSugarRow); nf.total_sugars.includes_added_sugars.daily_value = parseDailyValue(addedSugarRow); }

            // Lấy thành phần (Ingredients)
            const ingredientsHeaderRow = getNutritionRow(nutritionContainer, INGREDIENTS_HEADER_TEXT);
            if (ingredientsHeaderRow) {
                const nextRow = ingredientsHeaderRow.nextElementSibling;
                const ingredientsP = nextRow ? nextRow.querySelector('.column2 p, .column2') : null;

                if (ingredientsP) {
                    let ingredientsText = ingredientsP.innerText.split('\n')[0].trim();
                    ingredientsText = ingredientsText.replace(/／/g, '、');
                    productData.ingredients = ingredientsText.split(/,|、/).map(i => i.trim()).filter(Boolean);
                }
            } else { // Fallback cho trang US
                 const ingredientsH3 = Array.from(nutritionContainer.querySelectorAll('h3')).find(h => INGREDIENTS_HEADER_TEXT.some(header => h.innerText.trim() === header));
                 if (ingredientsH3 && ingredientsH3.nextElementSibling.tagName === 'P') {
                     let ingredientsText = ingredientsH3.nextElementSibling.innerText.split('\n')[0].trim();
                     productData.ingredients = ingredientsText.replace(/\.$/, '').split(',').map(i => i.trim()).filter(Boolean);
                 }
            }
        }
        
        allProductsData.push(productData);
    });

    return allProductsData;
}