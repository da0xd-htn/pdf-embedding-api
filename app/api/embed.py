from flask import Blueprint, request, send_file, jsonify
from PyPDF2 import PdfWriter, PdfReader, PdfMerger
from io import BytesIO
import logging
import os

embed_bp = Blueprint('embed', __name__, url_prefix='/api')

@embed_bp.route('/embed', methods=['POST'])
def embed_pdfs():
    """
    Properly embeds multiple PDFs into a main PDF
    ---
    Expects:
      - main_pdf: The base PDF file
      - files_to_embed: List of PDFs to embed
    Returns:
      - Combined PDF with all pages visible
    """
    try:
        # Validate input
        if 'main_pdf' not in request.files:
            return jsonify({"error": "Main PDF is required"}), 400
            
        files = request.files.getlist('files_to_embed')
        if len(files) > 4:
            return jsonify({"error": "Maximum 4 files allowed"}), 400

        # Create a merger for combining pages
        merger = PdfMerger()
        
        # Add main PDF first
        main_pdf = request.files['main_pdf']
        merger.append(BytesIO(main_pdf.read()))
        
        # Add other PDFs
        for file in files:
            if file.filename.lower().endswith('.pdf'):
                merger.append(BytesIO(file.read()))

        # Generate output
        output = BytesIO()
        merger.write(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='combined.pdf'  # Changed name for clarity
        )

    except Exception as e:
        logging.error(f"Embedding error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "PDF processing failed",
            "details": str(e)
        }), 500