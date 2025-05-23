from flask import Blueprint, request, send_file, jsonify
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from io import BytesIO
import logging
import json

embed_bp = Blueprint('embed', __name__, url_prefix='/api')

@embed_bp.route('/create_embedded_pdf', methods=['POST'])
def create_embedded_pdf():
    """
    Embed multiple PDFs into a single PDF with metadata
    ---
    tags:
      - PDF Operations
    consumes:
      - multipart/form-data
    parameters:
      - name: main_pdf
        in: formData
        type: file
        required: true
        description: The main PDF document
      - name: embedded_pdfs
        in: formData
        type: file
        required: true
        description: PDFs to embed
        multiple: true
    responses:
      200:
        description: Returns the merged PDF with embedded metadata
        content:
          application/pdf:
            schema:
              type: string
              format: binary
      400:
        description: Invalid input
      500:
        description: Internal server error
    """
    try:
        if 'main_pdf' not in request.files:
            return jsonify({"error": "Main PDF is required"}), 400
            
        main_pdf = request.files['main_pdf']
        embedded_pdfs = request.files.getlist('embedded_pdfs')
        
        if not embedded_pdfs:
            return jsonify({"error": "At least one PDF to embed is required"}), 400

        # Create merger and process files
        merger = PdfMerger()
        metadata = {
            "documents": [],
            "version": 1
        }
        current_page = 0
        
        # Process main PDF
        main_bytes = main_pdf.read()
        main_reader = PdfReader(BytesIO(main_bytes))
        merger.append(BytesIO(main_bytes))
        metadata["documents"].append({
            "start": current_page,
            "end": current_page + len(main_reader.pages) - 1,
            "name": "main.pdf"
        })
        current_page += len(main_reader.pages)
        
        # Process embedded PDFs
        for i, pdf in enumerate(embedded_pdfs):
            pdf_bytes = pdf.read()
            pdf_reader = PdfReader(BytesIO(pdf_bytes))
            merger.append(BytesIO(pdf_bytes))
            metadata["documents"].append({
                "start": current_page,
                "end": current_page + len(pdf_reader.pages) - 1,
                "name": f"embedded_{i}.pdf"
            })
            current_page += len(pdf_reader.pages)
        
        # Create final PDF with metadata
        merged_pdf = BytesIO()
        merger.write(merged_pdf)
        merged_pdf.seek(0)
        
        # Add metadata using PdfWriter
        writer = PdfWriter()
        writer.append(merged_pdf)
        
        # Add metadata as attachment
        writer.add_attachment(
            "_boundaries.json",
            json.dumps(metadata).encode('utf-8')
        )
        # Write final output
        output = BytesIO()
        writer.write(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='merged.pdf'
        )

    except Exception as e:
        logging.error(f"PDF merging failed: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500