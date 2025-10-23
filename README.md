# TTB Alcohol Label Verification App

This is a full-stack web application that simulates a simplified version of the TTB's label approval process by accepting an alcohol label image and form data, performing OCR verification, and providing a detailed compliance report.

## 🚀 Live Application

**[View Live Demo](#)** *(Replace with your deployed URL)*

## 📸 Application Preview

*(Add GIF or screenshot here)*

---

## ✨ Key Features

### Mandatory Field Verification

1. **Brand Name** - Ensures it is a legitimate brand
2. **Product Class/Type** - Verifies the alcohol category (e.g., "Kentucky Straight Bourbon Whiskey")
3. **Alcohol Content (ABV)** - Confirms the alcohol percentage
4. **Net Contents** - Validates the volume (e.g., "750 mL")
5. **Government Warning** - Checks for the required legal warning text

### Comprehensive Reporting
- Reports **all** discrepancies, not just the first error
- Provides clear pass/fail status for each label mismatch
- Displays the extracted OCR text for verification transparency

### Advanced Warning Validation
The Government Warning check has three distinct states:

1. **Missing** - The "GOVERNMENT WARNING" header is not found on the label
2. **Mismatch** - The header is present, but the content doesn't match the exact legal text:

```text
GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink 
alcoholic beverages during pregnancy because of the risk of birth defects. 
(2) Consumption of alcoholic beverages impairs your ability to drive a car or 
operate machinery, and may cause health problems.
```

3. **Match** - Both the header and content are present and correct

### No API Keys Required
This project runs entirely on open-source technologies with no external API dependencies.

---

## Technical Architecture

### Backend: Flask + Gunicorn

* **Technology:** I used Flask, a lightweight Python web framework, with Gunicorn as the production server.
* **Rational:** I needed a simple API endpoint to receive a form and return a JSON response. Flask's lightweight architecture was ideal since its single `/verify` endpoint handles form submission and returns JSON responses without unnecessary complexity. Gunicorn is also a very reliable and well-performing tool.

### Frontend: Vanilla HTML, CSS, and JavaScript

**Technology:** I used a standard HTML5, CSS3, and modern JavaScript (ES6+).

**Rationale:** For this project's UI, I only used a single form and a single results panel, which does not require complex state management. Hence, using a vanilla JavaScript with the `fetch` API creates a smooth single-page experience without the overhead of React or Vue (although this could definitely be built upon in the future\!). This approach keeps the bundle size small and the codebase accessible.

### OCR Engine: Tesseract (pytesseract)

**Technology:** I used Google's Tesseract OCR engine via the `pytesseract` Python wrapper

**Rationale:** Tesseract is an industry-standard, free, open-source OCR engine that provides quality text extraction without the cost or complexity of cloud APIs (AWS Textract, Google Vision, etc.). 

### Deployment Infrastructure: Docker + Render

**Containerization:** The app relies on Tesseract as a *system-level* dependency, not just a Python package. Hence, we need to containerize the app using **Docker**.

**Rationale:** `pytesseract` is just a wrapper; it needs the Tesseract engine to be installed on the host machine. Since Tesseract cannot be installed via `pip`, the `Dockerfile` (used for deployment) handles this by running:

```dockerfile
RUN apt-get update && apt-get install -y tesseract-ocr
```
before installing the Python requirements. This ensures that the app runs identically on the production server as it does on the local development environment.

**Platform:** I chose Render, which is a cloud platform that connects directly to GitHub.

**Rationale:** Render has a generous free tier and built-in Docker support (main reason why I chose this!). By connecting directly to the GitHub repository, it automatically builds the `Dockerfile` on every push, and manages the deployed web service, making continuous deployment simple and efficient.


## Coding Logic

### Image Pre-processing** 
I used Pillow (PIL) for my image pre-preprocessing. While pytesseract handles the actual text recognition, Pillow performs critical preprocessing steps that dramatically impact accuracy:

- **Grayscale conversion** - Removes color information that can confuse OCR engines, focusing solely on text contrast
- **Auto-contrast enhancement** - Adjusts brightness and contrast to make text more distinct from backgrounds
- **Format handling** - Processes various image formats (PNG, JPEG) and handles potential corruption 

This preprocessing pipeline in the `extract_text_from_image()` function is especially important for improving OCR accuracy since real-world label photos may have poor lighting, colored backgrounds, or glossy finishes that create reflections.

### Verification Process

**Design Pattern:** My app's core verification logic resides in `perform_verification()`, a "pure" function completely decoupled from Flask's web layer. This function takes in the form data and OCR text as inputs and returns a results dictionary. 

**Benefits:**
- **100% testable** - Can be imported directly into pytest without HTTP mocking (As you'll see in `test_app.py` (explained more in the Testing section), we can import this function directly into `pytest` and test all scenarios to make sure our verification process is correct without ever needing to simulate a web request.)
- **Framework agnostic** - Could be reused in different contexts (CLI, batch processing, etc.)
- **Clear separation of concerns** - Business logic isolated from I/O operations

### Government Warning Logic

The warning verification uses a three-stage approach:

1. **Presence check** - Searches for "GOVERNMENT WARNING" in the text
2. **Normalization** - Removes punctuation, converts to lowercase, collapses whitespace
3. **Content validation** - Compares normalized OCR text against normalized legal text

This approach is resilient to common OCR errors (e.g., `(1)` → `1)`, period → comma) while still enforcing compliance with the legal requirement.

### Pattern Matching Strategy

**Text Field Verification:**
- Uses regex with word boundaries to prevent partial matches (e.g., "Bourbon" won't match "Bourbon-like")
- Flexible whitespace handling accommodates OCR variations (spaces, newlines, multiple spaces)
- Hyphen flexibility allows "Old-Tom" to match "Old Tom"

**Numeric Field Verification (ABV):**
- Extracts numeric values with regex
- Uses negative lookbehind/lookahead to prevent substring matches (e.g., "45" won't match "1945")

---

## Local Development Setup

### Prerequisites

#### Install Tesseract OCR

Tesseract must be installed at the system level. `pytesseract` is only a wrapper and won't function without it.

**macOS** (using Homebrew):
```bash
brew install tesseract
```

**Windows**:
1. Download the installer from the [official Tesseract repository](https://github.com/UB-Mannheim/tesseract/wiki)
2. During installation, ensure you add Tesseract to your system PATH

**Linux** (Ubuntu/Debian):
```bash
sudo apt-get update && sudo apt-get install tesseract-ocr
```

#### Verify Installation
```bash
tesseract --version
```

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sichenz/TTB-Alcohol-Label-Verification-App.git
   cd TTB-Alcohol-Label-Verification-App
   ```

2. **Create a virtual environment:**

   Using venv:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

   Or using conda:
   ```bash
   conda create -n ttb python=3.12
   conda activate ttb
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the development server:**
   ```bash
   flask run
   ```

5. **Access the application:**
   Navigate to `http://127.0.0.1:5000` in your browser

---

## Testing

### Test Coverage

The test file (`test_app.py`) validates all required scenarios by using simulated OCR text directly into the `perform_verification()` function:

**Core Scenarios:**
- ✅ **Happy Path** - Perfect match across all fields (`test_scenario_all_match`)
- ✅ **Individual Mismatches** - Isolated test for each of the 5 fields
- ✅ **Multiple Mismatches** - Verifies that all errors are reported simultaneously
- ✅ **Edge Cases** - Tests partial match prevention, word boundaries, and multi-line text

**Warning-Specific Tests:**
- ✅ `test_scenario_warning_fully_missing` - Validates "missing" detection
- ✅ `test_scenario_warning_present_but_mismatched` - Validates content mismatch detection

**Error Handling:**
- ✅ `test_scenario_unreadable_image` - Handles blank/corrupted OCR output
- ✅ `test_scenario_no_partial_matches` - Prevents false positives from substring matches

### Running Tests

From the repository root:
```bash
pytest
```

For verbose output:
```bash
pytest -v
```

For coverage report:
```bash
pytest --cov=app --cov-report=html
```

Expected output: **11/11 tests passing** 
These tests make sure that our verification function is catching all forms of mismatches so getting 100% on this test file means that the verification function is correct.

---

## Using the Live Application

### Filling Out the Form

1. You can type your label information into the 5 required fields at any time.
2. The app **does not reload** on submission. If you make a typo and get a mismatch, your form data will remain intact. You can simply correct the field and click `Verify Label` again without re-typing everything.

### Uploading Label Images

**Supported Formats:** PNG, JPG, JPEG

1. The app accepts only **one image at a time**:

**Method 1 - Drag & Drop:**
- Drag an image file 
- Drop it onto the designated upload zone

**Method 2 - File Picker:**
- Click anywhere inside the upload zone
- Select an image from your files

2. Similarly, if you enter in the wrong image, it's not the end of the world! Simply just re-enter the correct image using one of the aforementioned two methods.

### Getting Results

1. After filling the form and uploading an image, click the `Verify Label` button.
2. A loading indicator will appear while the backend performs the OCR analysis.
3. The `Verification Results` panel on the right will then update:
   - Overall status (Success ✓ / Failure ✗)
   - Individual status for each of the 5 fields
   - Specific error messages for any mismatches
   - The raw OCR-extracted text for transparency

### Tips for Best Results

- Use high-resolution, well-lit images
- Ensure text on the label is in focus
- Avoid images with heavy reflections or glare
- Position the label to fill most of the frame
- Use images where text is horizontal and not distorted

---

## ⚠️ Known Limitations

### OCR Accuracy Dependencies

The application's accuracy is directly tied to Tesseract's OCR performance. Factors that may affect results:

- **Stylized or decorative fonts** - May be misread or not recognized
- **Low image quality** - Blurry, low-resolution, or poorly lit images reduce accuracy
- **Complex backgrounds** - Busy backgrounds can confuse text detection
- **Curved or distorted labels** - Non-flat surfaces may cause text distortion
- **Reflections and glare** - Can obscure text or create false characters

### Transparency Features

To help diagnose OCR issues, the app displays the **Extracted Text from Label** section, allowing you to:
- Verify what Tesseract actually read
- Identify OCR errors vs. actual label mismatches
- Determine if you need to use a different image

### Future Improvements

Potential enhancements for future versions:
- Image preprocessing recommendations in the UI
- Multiple language support (Tesseract supports 100+ languages)
- Batch processing for multiple labels
- Export results as PDF reports
- Integration with TTB's actual API (if available)

---

## 👤 Author

**Sichen Zhong**
- GitHub: [@sichenz](https://github.com/sichenz)
- Project Link: [https://github.com/sichenz/TTB-Alcohol-Label-Verification-App](https://github.com/sichenz/TTB-Alcohol-Label-Verification-App)

---

## 🙏 Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Google's open-source OCR engine
- [TTB](https://www.ttb.gov/) - Alcohol and Tobacco Tax and Trade Bureau for regulatory guidelines