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
        submitBtn.textContent = 'Embedding...';
        resultDiv.innerHTML = '<p class="processing">Processing...</p>';
        
        const formData = new FormData();
        const mainPdf = document.getElementById('main-pdf').files[0];
        const embeddedPdfs = document.getElementById('embedded-pdfs').files;
        
        // Validate input
        if (!mainPdf || embeddedPdfs.length === 0) {
            throw new Error("Please select a main PDF and at least one PDF to embed");
        }
        
        formData.append('main_pdf', mainPdf);
        Array.from(embeddedPdfs).forEach(pdf => {
            formData.append('embedded_pdfs', pdf);
        });
        
        const response = await fetch('/api/create_embedded_pdf', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Embedding failed');
        }
        
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        resultDiv.innerHTML = `
            <div class="success">
                <p>✓ PDFs embedded successfully!</p>
                <a href="${url}" download="embedded.pdf" class="download-btn">
                    Download Embedded PDF
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
        submitBtn.textContent = 'Embed PDFs';
    }
}

/**
 /**
 * PDF Extraction Form Handler
 */
function setupExtractForm() {
    const extractForm = document.getElementById('extract-form');
    if (!extractForm) return;

    extractForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        const resultDiv = document.getElementById('extract-result');
        
        try {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Analyzing PDF...';
            resultDiv.innerHTML = '<p class="processing">Detecting document boundaries...</p>';
            
            const formData = new FormData();
            formData.append('pdf_file', document.getElementById('extract-file').files[0]);
    
            const response = await fetch('/api/extract_embedded_pdf', {
                method: 'POST',
                body: formData
            });
    
            const result = await response.json();
            
            if (!result.success) {
                // More descriptive error message
                let errorMsg = result.error || 'Extraction failed';
                if (result.details) {
                    errorMsg += `: ${result.details}`;
                }
                throw new Error(errorMsg);
            }if (!result.success) {
                // More descriptive error message
                let errorMsg = result.error || 'Extraction failed';
                if (result.details) {
                    errorMsg += `: ${result.details}`;
                }
                throw new Error(errorMsg);
            }
    
            // Convert hex back to binary
            const zipData = new Uint8Array(result.zip_data.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
            const blob = new Blob([zipData], {type: 'application/zip'});
            const url = URL.createObjectURL(blob);
            
            resultDiv.innerHTML = `
                <div class="success-message">
                    <p>✓ Found ${result.documents_found} original documents!</p>
                    <a href="${url}" download="extracted_documents.zip" class="download-btn">
                        Download Documents (${(blob.size/1024).toFixed(1)} KB)
                    </a>
                </div>
            `;
            
        } catch (error) {
            resultDiv.innerHTML = `
                <div class="error-message">
                    <p>✗ ${error.message}</p>
                </div>
            `;
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Extract PDFs';
        }
    });
}

/**
 * Helper Functions
 */
function startProcessing(button, text = 'Processing...') {
    button.disabled = true;
    button.textContent = text;
}

function finishProcessing(button, defaultText = 'Submit') {
    button.disabled = false;
    button.textContent = defaultText;
}

function clearResults(container) {
    if (container) container.innerHTML = '';
}

function showSuccessResult(blob, container) {
    const url = URL.createObjectURL(blob);
    
    container.innerHTML = `
        <div class="success-message">
            <p>✓ PDFs combined successfully!</p>
            <div class="pdf-preview">
                <iframe src="${url}" style="width: 100%; height: 500px;"></iframe>
            </div>
            <a href="${url}" download="combined.pdf" class="download-btn">
                Download Combined PDF
            </a>
        </div>
    `;
}

function showExtractionResult(blob, container) {
    const url = URL.createObjectURL(blob);
    container.innerHTML = `
        <div class="success-message">
            <p>✓ PDFs extracted successfully!</p>
            <a href="${url}" download="extracted_files.zip" class="download-btn">
                Download Extracted Files (ZIP)
            </a>
        </div>
    `;
}

function showErrorResult(error, container) {
    container.innerHTML = `
        <div class="error-message">
            <p>✗ Error: ${error.message}</p>
        </div>
    `;
}

/**
 * Initialize all functionality
 */
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupEmbedForm();
    setupExtractForm();
});