import os
import re
from flask import Flask, request, render_template, jsonify
from PIL import Image, ImageOps
import pytesseract

app = Flask(__name__)

def extract_text_from_image(image_file):
    """
    Tries to open an image and extract text using OCR.
    Returns (ocr_text, error_message).
    """
    try:
        img = Image.open(image_file.stream)
        # Pre-process image for better OCR results (grayscale, increase contrast)
        img = ImageOps.grayscale(img)
        img = ImageOps.autocontrast(img, cutoff=0.5)
        
        ocr_text = pytesseract.image_to_string(img)
        
        if not ocr_text.strip():
            # This handles the unreadable image scenario
            return None, "Could not read text from the label image. Please try a clearer image."
            
        return ocr_text, None
        
    except Exception as e:
        print(f"Error processing image: {e}")
        # Handle corrupted files or other PIL/Tesseract errors
        return None, f"An error occurred during image processing: {e}. The image may be corrupted."

def perform_verification(form_data, ocr_text):
    """
    Performs the comparison logic against extracted OCR text using a refined regex approach.
    """
    LEGAL_WARNING_TEXT = "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."

    def normalize_text(text):
        """Lowercase, remove non-alphanumeric, collapse whitespace."""
        cleaned = re.sub(r'[^a-z0-9\s]', '', text.lower())
        return re.sub(r'\s+', ' ', cleaned).strip()

    normalized_ocr_for_warning = normalize_text(ocr_text)
    clean_legal_text = normalize_text(LEGAL_WARNING_TEXT)
    
    results = {
        "overall_status": "failure",
        "checks": [],
        "error": None,
        "ocr_text": ocr_text
    }

    # --- Get Form Data and Normalize Internal Whitespace ---
    brand_name = re.sub(r'\s+', ' ', form_data.get('brand_name', '').strip())
    product_class = re.sub(r'\s+', ' ', form_data.get('product_class', '').strip())
    alcohol_content = re.sub(r'\s+', ' ', form_data.get('alcohol_content', '').strip())
    net_contents = re.sub(r'\s+', ' ', form_data.get('net_contents', '').strip())

    # --- Perform Verification Checks ---

    def check_text_field(field_value, ocr_full_text):
        """
        Checks text fields using regex with word boundaries and flexible whitespace.
        Handles edge cases like hyphens, apostrophes, and accented characters.
        """
        if not field_value:
            return False
        
        # Normalize internal whitespace in field_value (already done above, but defensive)
        field_value = re.sub(r'\s+', ' ', field_value)
        escaped_value = re.escape(field_value)
        # This handles cases where OCR might have newlines or multiple spaces
        pattern_core = escaped_value.replace(r'\ ', r'\s+')
        # This handles "Straight-Bourbon" matching "Straight Bourbon" and vice versa
        pattern_core = pattern_core.replace(r'\-', r'[\s\-]*')
        
        # Add word boundaries with negative lookahead
        # \b works differently with non-ASCII chars, but for ASCII alphanumeric it's fine
        # The negative lookahead prevents "Bourbon" from matching "Bourbon-like"
        pattern = r"(?<![a-zA-Z0-9])" + pattern_core + r"(?![a-zA-Z0-9\-])"
        match = re.search(pattern, ocr_full_text, re.IGNORECASE)
        return bool(match)

    # Check 1: Brand Name (Precise Regex)
    brand_match = check_text_field(brand_name, ocr_text)
    results["checks"].append({
        "field": "Brand Name",
        "form_value": brand_name,
        "match": brand_match,
        "message": f"Brand name '{brand_name}' not found on label." if not brand_match else "Brand name on label matches form."
    })

    # Check 2: Product Class/Type (Precise Regex)
    class_match = check_text_field(product_class, ocr_text)
    results["checks"].append({
        "field": "Product Class/Type",
        "form_value": product_class,
        "match": class_match,
        "message": f"Product class '{product_class}' not found on label." if not class_match else "Product class on label matches form."
    })

    # Check 3: Alcohol Content (ABV)
    num_match = re.search(r'(\d+(?:\.\d+)?)', alcohol_content)
    abv_match = False
    if num_match:
        num_only = num_match.group(1)
        # Use negative lookbehind/lookahead to prevent matching as part of larger number
        # e.g., "45" shouldn't match "1945" or "450"
        abv_pattern = r"(?<!\d)" + re.escape(num_only) + r"(?!\d)"
        abv_match = bool(re.search(abv_pattern, ocr_text))
    
    results["checks"].append({
        "field": "Alcohol Content (ABV)",
        "form_value": alcohol_content,
        "match": abv_match,
        "message": f"Alcohol content '{alcohol_content}' not found on label." if not abv_match else "Alcohol content on label matches form."
    })

    # Check 4: Net Contents (Precise Regex)
    net_match = check_text_field(net_contents, ocr_text)
    results["checks"].append({
        "field": "Net Contents",
        "form_value": net_contents,
        "match": net_match,
        "message": f"Net contents '{net_contents}' not found on label." if not net_match else "Net contents on label matches form."
    })

    # Check 5: Government Warning (Uses normalization + substring)
    warning_present = "government warning" in normalized_ocr_for_warning 
    warning_matches_content = clean_legal_text in normalized_ocr_for_warning 
    
    warning_match = False
    warning_message = ""
    if not warning_present:
        warning_match = False
        warning_message = "Government warning text is missing from the label."
    elif not warning_matches_content:
        warning_match = False
        warning_message = "Government warning text is present, but it does not match the legal government warning statement."
    else: 
        warning_match = True
        warning_message = "Government warning text is present and matches the legal statement."

    results["checks"].append({
        "field": "Government Warning",
        "form_value": "Full Legal Text Required",
        "match": warning_match,
        "message": warning_message
    })

    # --- Determine Overall Status ---
    if all(check["match"] for check in results["checks"]):
        results["overall_status"] = "success"
    else:
        results["overall_status"] = "failure"
            
    return results

# --- API Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify', methods=['POST'])
def handle_verification():
    if 'label_image' not in request.files: return jsonify({"error": "No image file provided."}), 400
    file = request.files['label_image']
    if file.filename == '': return jsonify({"error": "No selected file."}), 400
    allowed_extensions = {'png', 'jpg', 'jpeg'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
         return jsonify({"error": "Invalid image format. Please use PNG, JPG, or JPEG."}), 400

    ocr_text, error = extract_text_from_image(file)
    if error: return jsonify({"error": error}), 400
    
    form_data = request.form
    results = perform_verification(form_data, ocr_text)
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))