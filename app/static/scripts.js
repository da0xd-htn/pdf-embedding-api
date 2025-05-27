/**
 * Tab Switching Functionality
 */
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
}

/**
 * PDF Embedding Form Handler
 */
function setupEmbedForm() {
    const embedForm = document.getElementById('embed-form');
    if (!embedForm) return;

    embedForm.addEventListener('submit', handleEmbedFormSubmit);
}

async function handleEmbedFormSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const resultDiv = document.getElementById('embed-result');
    
    try {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';
        resultDiv.innerHTML = '<p class="processing">Creating PDF container...</p>';
        
        const pdfFiles = document.getElementById('pdf-files').files;
        if (pdfFiles.length === 0) {
            throw new Error("Please select at least one PDF");
        }

        // Validate PDF files
        for (let file of pdfFiles) {
            if (!file.name.toLowerCase().endsWith('.pdf')) {
                throw new Error(`File "${file.name}" is not a PDF`);
            }
        }

        const formData = new FormData();
        Array.from(pdfFiles).forEach(file => {
            formData.append('pdf_files', file);
        });

        const response = await fetch('/api/create_embedded_pdf', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let errorMessage = 'Embedding failed';
            try {
                const error = await response.json();
                errorMessage = error.error || errorMessage;
            } catch {
                errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        resultDiv.innerHTML = `
            <div class="success">
                <p>✓ ${pdfFiles.length} PDFs embedded successfully!</p>
                <p>Total size: ${(blob.size / 1024 / 1024).toFixed(2)} MB</p>
                <a href="${url}" download="embedded_container.pdf" class="download-btn">
                    Download PDF Container
                </a>
            </div>
        `;
        
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="error">
                <p>✗ ${error.message}</p>
            </div>
        `;
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create PDF Container';
    }
}

/**
 * PDF Extraction Form Handler
 */
function setupExtractForm() {
    const extractForm = document.getElementById('extract-form');
    if (!extractForm) return;

    extractForm.addEventListener('submit', handleExtractFormSubmit);
}

async function handleExtractFormSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const resultDiv = document.getElementById('extract-result');
    
    try {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Extracting...';
        resultDiv.innerHTML = '<p class="processing">Extracting embedded files...</p>';
        
        const pdfFile = document.getElementById('extract-file').files[0];
        if (!pdfFile) {
            throw new Error("Please select a PDF file");
        }

        if (!pdfFile.name.toLowerCase().endsWith('.pdf')) {
            throw new Error("Selected file is not a PDF");
        }

        const formData = new FormData();
        formData.append('pdf_file', pdfFile);

        const response = await fetch('/api/extract_embedded_pdf', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let errorMessage = 'Extraction failed';
            try {
                const error = await response.json();
                errorMessage = error.error || errorMessage;
                if (error.hint) {
                    errorMessage += `\n\nHint: ${error.hint}`;
                }
            } catch {
                errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        resultDiv.innerHTML = `
            <div class="success">
                <p>✓ Embedded files extracted successfully!</p>
                <p>Archive size: ${(blob.size / 1024 / 1024).toFixed(2)} MB</p>
                <a href="${url}" download="extracted_pdfs.zip" class="download-btn">
                    Download Extracted Files (ZIP)
                </a>
            </div>
        `;
        
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="error">
                <p style="white-space: pre-line;">✗ ${error.message}</p>
            </div>
        `;
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Extract PDFs';
    }
}

/**
 * Helper Functions
 */
function validatePdfFile(file) {
    if (!file) return false;
    return file.name.toLowerCase().endsWith('.pdf') && file.type === 'application/pdf';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Initialize all functionality
 */
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupEmbedForm();
    setupExtractForm();
    
    // Add file validation feedback
    const pdfFilesInput = document.getElementById('pdf-files');
    const extractFileInput = document.getElementById('extract-file');
    
    if (pdfFilesInput) {
        pdfFilesInput.addEventListener('change', (e) => {
            const files = e.target.files;
            let validCount = 0;
            for (let file of files) {
                if (file.name.toLowerCase().endsWith('.pdf')) {
                    validCount++;
                }
            }
            
            if (validCount !== files.length) {
                alert(`${validCount} of ${files.length} selected files are valid PDFs`);
            }
        });
    }
    
    if (extractFileInput) {
        extractFileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file && !file.name.toLowerCase().endsWith('.pdf')) {
                alert('Please select a PDF file');
                e.target.value = '';
            }
        });
    }
});