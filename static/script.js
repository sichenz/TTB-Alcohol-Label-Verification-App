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

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropZone.classList.add('dragover');
    }

    function unhighlight() {
        dropZone.classList.remove('dragover');
    }

    dropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
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
        e.preventDefault(); 
        
        loadingIndicator.classList.remove('hidden');
        resultsContent.classList.add('hidden'); 
        submitButton.disabled = true;
        submitButton.textContent = 'Processing...';

        const formData = new FormData(form);

        try {
            const response = await fetch('/verify', { // Assuming your backend endpoint is /verify
                method: 'POST',
                body: formData,
            });

            const results = await response.json();
            displayResults(results);

        } catch (error) {
            console.error('Submission error:', error);
            resultsSummary.innerHTML = '&#10060; An unexpected error occurred. Please try again.';
            resultsSummary.className = 'failure';
        } finally {
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
        
        if (results.error) {
            resultsSummary.innerHTML = `&#10060; Error: ${results.error}`;
            resultsSummary.className = 'failure';
            return;
        }

        if (results.overall_status === 'success') {
            resultsSummary.innerHTML = '&#9989; Success: The label matches the form data.';
            resultsSummary.className = 'success';
        } else {
            resultsSummary.innerHTML = '&#10060; Failure: The label does not match the form.';
            resultsSummary.className = 'failure';
        }

        results.checks.forEach(check => {
            const item = document.createElement('div');
            item.className = 'result-item';

            const iconClass = check.match ? 'match' : 'mismatch';
            const icon = check.match ? '&#9989;' : '&#10060;';
            
            const message = check.match 
                ? `<strong>${check.field}:</strong> <span>Matched. (Form: '${check.form_value}')</span>`
                : `<strong>${check.field}:</strong> <span>${check.message} (Form: '${check.form_value}')</span>`;

            item.innerHTML = `
                <div class="result-icon ${iconClass}">${icon}</div>
                <div class="result-text">${message}</div>
            `;
            resultsDetails.appendChild(item);
        });

        if (results.ocr_text) {
            ocrTextContent.textContent = results.ocr_text;
            ocrOutput.classList.remove('hidden');
        } else {
            ocrOutput.classList.add('hidden');
        }
    }
    
    // --- Theme Switch Logic ---
    
    const themeSelect = document.getElementById('theme-select');
    
    // Load saved theme or default to 'forest'
    const currentTheme = localStorage.getItem('theme') || 'forest';
    document.body.dataset.theme = currentTheme === 'forest' ? '' : currentTheme;
    themeSelect.value = currentTheme;

    themeSelect.addEventListener('change', () => {
        const selectedTheme = themeSelect.value;
        // For 'forest' (default), remove the data-theme attribute
        // For other themes, set the data-theme attribute
        if (selectedTheme === 'forest') {
            document.body.removeAttribute('data-theme');
        } else {
            document.body.dataset.theme = selectedTheme;
        }
        // Save the choice to localStorage
        localStorage.setItem('theme', selectedTheme);
    });

});