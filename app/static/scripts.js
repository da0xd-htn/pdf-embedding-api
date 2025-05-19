/**
 * PDF Embedding Form Handler
 */
document.addEventListener('DOMContentLoaded', () => {
    const embedForm = document.getElementById('embed-form');
    
    if (embedForm) {
        embedForm.addEventListener('submit', handleEmbedFormSubmit);
    }
});

async function handleEmbedFormSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const resultDiv = document.getElementById('result') || createResultDiv(form);
    
    try {
        // UI Feedback
        startProcessing(submitBtn);
        clearResults(resultDiv);
        
        // Prepare Form Data
        const formData = prepareFormData();
        
        // API Request
        const response = await fetch('/api/embed', {
            method: 'POST',
            body: formData
        });

        // Handle Response
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Embedding failed');
        }

        // Show Success
        const blob = await response.blob();
        showSuccessResult(blob, resultDiv);
        
    } catch (error) {
        showErrorResult(error, resultDiv);
    } finally {
        finishProcessing(submitBtn);
    }
}

// Helper Functions
function createResultDiv(form) {
    const div = document.createElement('div');
    div.id = 'result';
    form.appendChild(div);
    return div;
}

function startProcessing(button) {
    button.disabled = true;
    button.textContent = 'Processing...';
}

function finishProcessing(button) {
    button.disabled = false;
    button.textContent = 'Embed Files';
}

function clearResults(container) {
    container.innerHTML = '';
}

function prepareFormData() {
    const formData = new FormData();
    const files = document.getElementById('embed-files').files;
    
    if (files.length === 0) {
        throw new Error("Please select at least one PDF");
    }
    
    // Add main PDF (first file)
    formData.append('main_pdf', files[0]);
    
    // Add files to embed (remaining files)
    for (let i = 1; i < files.length; i++) {
        formData.append('files_to_embed', files[i]);
    }
    
    return formData;
}

function showSuccessResult(blob, container) {
    const url = URL.createObjectURL(blob);
    
    // Create preview iframe
    const previewHTML = `
        <div class="pdf-preview">
            <iframe src="${url}" style="width: 100%; height: 500px;"></iframe>
        </div>
    `;
    
    container.innerHTML = `
        <div class="success-message">
            <p>✓ PDFs combined successfully!</p>
            ${previewHTML}
            <a href="${url}" download="combined.pdf" class="download-btn">
                Download Combined PDF
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