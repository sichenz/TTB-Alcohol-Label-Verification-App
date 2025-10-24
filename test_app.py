import pytest
from app import perform_verification

@pytest.fixture
def base_form_data():
    """This is our "correct" form data"""
    return {
        'brand_name': 'Old Tom Distillery',
        'product_class': 'Kentucky Straight Bourbon Whiskey',
        'alcohol_content': '45%',
        'net_contents': '750 mL'
    }

@pytest.fixture
def testing_ocr_text(): 
    """
    This is our "perfect" baseline OCR text. 
    DO NOT EDIT THIS to test scenarios. The test functions below
    will create their own "bad" text from this.
    """
    return """
    OLD TOM DISTILLERY
    EST. 1902
    KENTUCKY STRAIGHT BOURBON WHISKEY
    45% Alc./Vol. (90 Proof)
    750 mL
    DISTILLED AND BOTTLED BY OLD TOM, FRANKFORT, KY
    GOVERNMENT WARNING: (1) According to the Surgeon General, women
    should not drink alcoholic beverages during pregnancy because of the risk of
    birth defects. (2) Consumption of alcoholic beverages impairs your ability to 
    drive a car or operate machinery, and may cause health problems.
    """

# --- The "Happy Path" ---

def test_scenario_all_match(base_form_data, testing_ocr_text):
    """
    Tests the "matching info" scenario. All fields should pass.
    """
    results = perform_verification(base_form_data, testing_ocr_text)
    
    assert results["overall_status"] == "success"
    assert all(check["match"] for check in results["checks"])
    assert "matches the legal statement" in results["checks"][4]["message"]

# --- Individual Mismatch Scenarios ---

def test_scenario_brand_mismatch(base_form_data, testing_ocr_text):
    """
    Tests the "mismatched info" scenario for Brand Name.
    This test takes the "perfect" text and only breaks the brand name.
    """
    bad_text = testing_ocr_text.replace("OLD TOM DISTILLERY", "WRONG BRAND") 
    results = perform_verification(base_form_data, bad_text)
    
    assert results["overall_status"] == "failure"
    assert results["checks"][0]["match"] is False  # Brand fails
    assert "not found" in results["checks"][0]["message"]
    # Check that others still pass
    assert results["checks"][1]["match"] is True   # Class passes
    assert results["checks"][3]["match"] is True   # Net passes
    assert results["checks"][4]["match"] is True   # Warning passes

def test_scenario_product_class_mismatch(base_form_data, testing_ocr_text):
    """
    Tests the "mismatched info" scenario for Product Class/Type.
    This test takes the "perfect" text and only breaks the class.
    """
    bad_text = testing_ocr_text.replace("KENTUCKY STRAIGHT BOURBON WHISKEY", "VODKA") 
    results = perform_verification(base_form_data, bad_text)
    
    assert results["overall_status"] == "failure"
    assert results["checks"][1]["match"] is False  # Class fails
    assert "not found" in results["checks"][1]["message"]
    # Check that others still pass
    assert results["checks"][0]["match"] is True   # Brand passes
    assert results["checks"][3]["match"] is True   # Net passes
    assert results["checks"][4]["match"] is True   # Warning passes

def test_scenario_alcohol_content_mismatch(base_form_data, testing_ocr_text):
    """
    Tests the "mismatched info" scenario for Alcohol Content (ABV).
    This test takes the "perfect" text and only breaks the ABV.
    """
    bad_text = testing_ocr_text.replace("45%", "12.5%") 
    results = perform_verification(base_form_data, bad_text)
    
    assert results["overall_status"] == "failure"
    assert results["checks"][2]["match"] is False  # ABV fails
    assert "not found" in results["checks"][2]["message"]
    # Check that others still pass
    assert results["checks"][0]["match"] is True   # Brand passes
    assert results["checks"][1]["match"] is True   # Class passes
    assert results["checks"][4]["match"] is True   # Warning passes

def test_scenario_net_contents_mismatch(base_form_data, testing_ocr_text):
    """
    Tests the "mismatched info" scenario for Net Contents.
    This test takes the "perfect" text and only breaks the net contents.
    """
    bad_text = testing_ocr_text.replace("750 mL", "1.5 L") 
    results = perform_verification(base_form_data, bad_text)
    
    assert results["overall_status"] == "failure"
    assert results["checks"][3]["match"] is False  # Net fails
    assert "not found" in results["checks"][3]["message"]
    # Check that others still pass
    assert results["checks"][0]["match"] is True   # Brand passes
    assert results["checks"][4]["match"] is True   # Warning passes
    assert results["checks"][1]["match"] is True   # Class passes

# --- Multiple Mismatch Scenarios ---

def test_scenario_multiple_mismatches_1(base_form_data, testing_ocr_text):
    """
    This test breaks Brand, ABV, and Warning.
    """
    bad_text = testing_ocr_text.replace("OLD TOM DISTILLERY", "WRONG BRAND") 
    bad_text = bad_text.replace("45%", "12%")
    bad_text = bad_text.replace("According to the Surgeon General", "The government says")
    
    results = perform_verification(base_form_data, bad_text)
    
    assert results["overall_status"] == "failure"
    assert results["checks"][0]["match"] is False # Brand
    assert results["checks"][2]["match"] is False # ABV
    assert results["checks"][4]["match"] is False # Warning
    assert "does not match" in results["checks"][4]["message"]
    assert results["checks"][1]["match"] is True # Class
    assert results["checks"][3]["match"] is True # Net Contents

def test_scenario_multiple_mismatches_2(base_form_data, testing_ocr_text):
    """
    This test breaks Class and Net Contents, but leaves Warning intact.
    """
    bad_text = testing_ocr_text.replace("KENTUCKY STRAIGHT BOURBON WHISKEY", "GIN") 
    bad_text = bad_text.replace("750 mL", "1 L")
    
    results = perform_verification(base_form_data, bad_text)
    
    assert results["overall_status"] == "failure"
    assert results["checks"][1]["match"] is False # Class
    assert results["checks"][3]["match"] is False # Net Contents
    assert results["checks"][0]["match"] is True # Brand
    assert results["checks"][2]["match"] is True # ABV
    assert results["checks"][4]["match"] is True # Warning

# --- WARNING Tests ---

def test_scenario_warning_fully_missing(base_form_data, testing_ocr_text):
    """
    Tests the scenario where the entire warning (header and content) is missing.
    """
    # Replace header and empty out content
    bad_text = testing_ocr_text.replace("GOVERNMENT WARNING:", "HEALTH INFO:") 
    bad_text = bad_text.replace("According to the Surgeon General", "Please drink responsibly")
    results = perform_verification(base_form_data, bad_text)
    
    assert results["overall_status"] == "failure"
    assert results["checks"][4]["field"] == "Government Warning"
    assert results["checks"][4]["match"] is False
    # The app logic correctly identifies the missing header as the primary fault
    assert "missing from the label" in results["checks"][4]["message"]

def test_scenario_warning_present_but_mismatched(base_form_data, testing_ocr_text):
    """
    Tests the scenario where 'GOVERNMENT WARNING' is present, but the
    subsequent text is incorrect.
    """
    bad_text = testing_ocr_text.replace("According to the Surgeon General", "The government says") 
    results = perform_verification(base_form_data, bad_text)
    
    assert results["overall_status"] == "failure"
    assert results["checks"][4]["field"] == "Government Warning"
    assert results["checks"][4]["match"] is False
    assert "does not match the legal" in results["checks"][4]["message"]

# --- Other Scenarios ---

def test_scenario_unreadable_image(base_form_data):
    """
    Tests the "unreadable image" scenario (when OCR returns no text).
    """
    empty_text = ""
    results = perform_verification(base_form_data, empty_text)
    
    assert results["overall_status"] == "failure"
    assert all(not check["match"] for check in results["checks"])
    assert "missing" in results["checks"][4]["message"]

def test_scenario_no_partial_matches():
    """
    Tests that the word boundary fix prevents partial matches and
    handles multi-line text.
    """
    # 1. Test Brand Name partial match (e.g., "Old Tom" vs "OldTombstone")
    form_data_brand = {'brand_name': 'Old Tom', 'product_class': 'N/A', 'alcohol_content': 'N/A', 'net_contents': 'N/A'}
    ocr_text_brand = "This is the OldTombstone Distillery"
    results_brand = perform_verification(form_data_brand, ocr_text_brand)
    assert results_brand["checks"][0]["match"] is False # "Old Tom" should NOT match "OldTombstone"
    
    # 2. Test ABV partial match (e.g., "45" vs "1945")
    form_data_abv = {'brand_name': 'N/A', 'product_class': 'N/A', 'alcohol_content': '45', 'net_contents': 'N/A'}
    ocr_text_abv = "Lot number 1945"
    results_abv = perform_verification(form_data_abv, ocr_text_abv)
    assert results_abv["checks"][2]["match"] is False # "45" should NOT match "1945"
    
    # 3. Test Net Contents with punctuation 
    form_data_net_pass = {'brand_name': 'N/A', 'product_class': 'N/A', 'alcohol_content': 'N/A', 'net_contents': '750 mL'}
    ocr_text_net_pass = "Volume: (750 mL)." # Parens and periods are boundaries
    results_net_pass = perform_verification(form_data_net_pass, ocr_text_net_pass)
    assert results_net_pass["checks"][3]["match"] is True # "750 mL" SHOULD match "(750 mL)."
    
    # 4. Test Product Class partial match (e.g., "Bourbon" vs "Bourbon-like")
    form_data_class_partial = {'brand_name': 'N/A', 'product_class': 'Bourbon', 'alcohol_content': 'N/A', 'net_contents': 'N/A'}
    ocr_text_class_partial = "A Bourbon-like Whiskey"
    results_class_partial = perform_verification(form_data_class_partial, ocr_text_class_partial)
    assert results_class_partial["checks"][1]["match"] is False # "Bourbon" should NOT match "Bourbon-like"

    # 5. Test Product Class newline fix (from manual testing)
    form_data_class_newline = {'brand_name': 'N/A', 'product_class': 'Rum with Coconut Liqueur', 'alcohol_content': 'N/A', 'net_contents': 'N/A'}
    ocr_text_class_newline = """
    IMPORTS
    RUM WITH
    COCONUT LIQUEUR
    18% ALC/VOL. 200 ML
    """
    results_class_newline = perform_verification(form_data_class_newline, ocr_text_class_newline)
    assert results_class_newline["checks"][1]["match"] is True # "Rum with Coconut Liqueur" SHOULD match

def test_hyphenated_values():
    """Test hyphen vs space variations"""
    form = {'brand_name': 'Old-Tom', 'product_class': 'N/A', 
            'alcohol_content': 'N/A', 'net_contents': 'N/A'}
    ocr = "OLD TOM DISTILLERY"  # space instead of hyphen
    results = perform_verification(form, ocr)
    assert results["checks"][0]["match"] is True

def test_multiple_spaces_in_form():
    """Test extra whitespace in form input"""
    form = {'brand_name': 'Old  Tom', 'product_class': 'N/A', 
            'alcohol_content': 'N/A', 'net_contents': 'N/A'}
    ocr = "OLD TOM"
    results = perform_verification(form, ocr)
    assert results["checks"][0]["match"] is True

def test_abv_within_larger_number():
    """Test ABV doesn't match as substring of larger number"""
    form = {'brand_name': 'N/A', 'product_class': 'N/A', 
            'alcohol_content': '45%', 'net_contents': 'N/A'}
    ocr = "Established 1945, lot 450"
    results = perform_verification(form, ocr)
    assert results["checks"][2]["match"] is False