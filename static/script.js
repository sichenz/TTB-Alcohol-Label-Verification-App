document.addEventListener('DOMContentLoaded', () => {
    
    // Form and result elements
    const form = document.getElementById('verification-form');
    const submitButton = document.getElementById('submit-button');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultsSummary = document.getElementById('results-summary');
    const resultsDetails = document.getElementById('results-details');
    const ocrOutput = document.getElementById('ocr-output');
    const ocrTextContent = document.getElementById('ocr-text-content');
    const resultsContent = document.getElementById('results-content');
    
    // File input and drag-and-drop elements
    const imageInput = document.getElementById('label-image-input');
    const dropZone = document.getElementById('drop-zone');
    const imagePreview = document.getElementById('image-preview');

    // --- Drag and Drop Logic ---

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop zone when item is dragged over
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    // Un-highlight drop zone when item leaves
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropZone.classList.add('dragover');
    }

    function unhighlight(e) {
        dropZone.classList.remove('dragover');
    }

    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        // Update the file input with the dropped file
        imageInput.files = files;
        // Manually trigger the 'change' event to update the preview
        imageInput.dispatchEvent(new Event('change'));
    }

    // --- Image Preview Logic  ---
    imageInput.addEventListener('change', () => {
        const file = imageInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreview.classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        } else {
            imagePreview.src = '#';
            imagePreview.classList.add('hidden');
        }
    });

    // --- Async Form Submission ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault(); // Prevent default page reload
        
        // 1. Show loading indicator and clear old results
        loadingIndicator.classList.remove('hidden');
        resultsContent.classList.add('hidden'); // Hide old results
        submitButton.disabled = true;
        submitButton.textContent = 'Processing...';

        // 2. Prepare form data
        const formData = new FormData(form);

        try {
            // 3. Send data to backend
            const response = await fetch('/verify', {
                method: 'POST',
                body: formData,
            });

            const results = await response.json();

            // 4. Display results
            displayResults(results);

        } catch (error) {
            // Handle network or server errors
            console.error('Submission error:', error);
            resultsSummary.innerHTML = '&#10060; An unexpected error occurred. Please check the console and try again.';
            resultsSummary.className = 'failure';
        } finally {
            // 5. Hide loading indicator and show results
            loadingIndicator.classList.add('hidden');
            resultsContent.classList.remove('hidden');
            submitButton.disabled = false;
            submitButton.textContent = 'Verify Label';
        }
    });

    /**
     * Renders the verification results on the page.
     */
    function displayResults(results) {
        resultsSummary.innerHTML = '';
        resultsDetails.innerHTML = '';
        resultsSummary.classList.remove('success', 'failure');
        
        // Handle a backend error (e.g., unreadable image)
        if (results.error) {
            resultsSummary.innerHTML = `&#10060; Error: ${results.error}`;
            resultsSummary.className = 'failure';
            return;
        }

        // Display Overall Status
        if (results.overall_status === 'success') {
            resultsSummary.innerHTML = '&#9989; Success: The label matches the form data.';
            resultsSummary.className = 'success';
        } else {
            resultsSummary.innerHTML = '&#10060; Failure: The label does not match the form.';
            resultsSummary.className = 'failure';
        }

        // Display Detailed Checklist
        results.checks.forEach(check => {
            const item = document.createElement('div');
            item.className = 'result-item';

            const icon = check.match ? '&#9989;' : '&#10060;';
            const iconClass = check.match ? 'match' : 'mismatch';
            
            const message = check.match 
                ? `<strong>${check.field}:</strong> <span>Matched. (Form: '${check.form_value}')</span>`
                : `<strong>${check.field}:</strong> <span>${check.message} (Form: '${check.form_value}')</span>`;

            item.innerHTML = `
                <div class="result-icon ${iconClass}">${icon}</div>
                <div class="result-text">${message}</div>
            `;
            resultsDetails.appendChild(item);
        });

        // Show the raw OCR output for transparency
        if (results.ocr_text) {
            ocrTextContent.textContent = results.ocr_text;
            ocrOutput.classList.remove('hidden');
        } else {
            ocrOutput.classList.add('hidden');
        }
    }
});