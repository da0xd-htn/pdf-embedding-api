from flask import Blueprint, request, jsonify
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import zipfile
import logging
import json

extract_bp = Blueprint('extract', __name__, url_prefix='/api')

def detect_page_boundaries(reader):
    """Fallback method to detect document boundaries"""
    boundaries = []
    current_doc = [0]  # Start with first page
    
    for i in range(1, len(reader.pages)):
        prev = reader.pages[i-1]
        curr = reader.pages[i]
        
        # Check for significant layout changes
        if (prev.mediabox != curr.mediabox or 
            abs(len(prev.extract_text() or "") - len(curr.extract_text() or "")) > 200):
            boundaries.append(current_doc)
            current_doc = [i]
        else:
            current_doc.append(i)
    
    if current_doc:
        boundaries.append(current_doc)
    
    return [
        {
            "start": doc[0],
            "end": doc[-1],
            "name": f"document_{i+1}.pdf"
        }
        for i, doc in enumerate(boundaries)
    ]

@extract_bp.route('/extract_embedded_pdf', methods=['POST'])
def extract_embedded_pdf():
    """
    Extract embedded PDFs from a merged PDF
    ---
    tags:
      - PDF Operations
    consumes:
      - multipart/form-data
    parameters:
      - name: pdf_file
        in: formData
        type: file
        required: true
        description: The merged PDF containing embedded documents
    responses:
      200:
        description: Returns a ZIP file containing extracted PDFs
        schema:
          type: object
          properties:
            success:
              type: boolean
            documents_found:
              type: integer
            zip_data:
              type: string
              description: Hex-encoded ZIP file data
      400:
        description: Invalid input
      500:
        description: Internal server error
    """
    try:
        if 'pdf_file' not in request.files:
            return jsonify({"error": "PDF file is required"}), 400

        pdf_file = request.files['pdf_file']
        reader = PdfReader(BytesIO(pdf_file.read()))
        
        # Try to find metadata first
        metadata = None
        if hasattr(reader, 'embedded_files'):
            for name, (_, data) in reader.embedded_files.items():
                if name == "_boundaries.json":
                    metadata = json.loads(data.get_data().decode('utf-8'))
                    break
        
        # Fallback to boundary detection
        if not metadata:
            if len(reader.pages) < 2:
                return jsonify({"error": "Not a valid merged PDF"}), 400
            metadata = {"documents": detect_page_boundaries(reader)}

        # Extract documents
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zipf:
            for doc in metadata["documents"]:
                writer = PdfWriter()
                for page_num in range(doc["start"], doc["end"] + 1):
                    writer.add_page(reader.pages[page_num])
                
                pdf_data = BytesIO()
                writer.write(pdf_data)
                pdf_data.seek(0)
                zipf.writestr(doc["name"], pdf_data.getvalue())

        zip_buffer.seek(0)
        return jsonify({
            "success": True,
            "documents_found": len(metadata["documents"]),
            "zip_data": zip_buffer.getvalue().hex(),
            "message": "Used fallback boundary detection" if not metadata else ""
        })

    except Exception as e:
        logging.error(f"Extraction failed: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Failed to extract documents",
            "details": str(e)
        }), 500