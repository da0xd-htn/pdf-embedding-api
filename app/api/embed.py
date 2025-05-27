from flask import Blueprint, request, send_file, jsonify
from flasgger.utils import swag_from
from PyPDF2 import PdfWriter, PdfReader
from io import BytesIO
import logging

embed_bp = Blueprint('embed', __name__)

@embed_bp.route('/create_embedded_pdf', methods=['POST'])
@swag_from({
    'tags': ['PDF Operations'],
    'summary': 'Embed multiple PDFs into a single PDF container',
    'description': 'Takes multiple PDF files and embeds them as attachments in a single PDF container',
    'consumes': ['multipart/form-data'],
    'parameters': [{
        'name': 'pdf_files',
        'in': 'formData',
        'type': 'file',
        'required': True,
        'description': 'PDF files to embed (multiple files allowed)',
        'collectionFormat': 'multi'
    }],
    'responses': {
        200: {
            'description': 'PDF container with embedded files',
            'schema': {
                'type': 'file'
            }
        },
        400: {
            'description': 'Bad request - no files uploaded',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Server error during embedding',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def embed_pdfs():
    """
    Embed multiple PDF files into a single PDF container as attachments
    """
    try:
        files = request.files.getlist('pdf_files')
        if not files or all(file.filename == '' for file in files):
            return jsonify({"error": "No files uploaded"}), 400
        
        # Validate that all files are PDFs
        valid_files = []
        for file in files:
            if file and file.filename and file.filename.lower().endswith('.pdf'):
                valid_files.append(file)
            else:
                return jsonify({"error": f"File {file.filename} is not a PDF"}), 400
        
        writer = PdfWriter()
        
        # Add a blank page as the main content (container)
        writer.add_blank_page(width=612, height=792)  # Standard US Letter size
        
        # Embed each PDF file as attachment
        embedded_count = 0
        for i, file in enumerate(valid_files):
            try:
                # Read file data as binary
                file_data = file.read()
                
                # Validate PDF by trying to read it
                if not file_data.startswith(b'%PDF'):
                    return jsonify({"error": f"File {file.filename} is not a valid PDF"}), 400
                
                # Use original filename (no need for unique names as PyPDF2 handles duplicates)
                filename = file.filename
                
                # Add as attachment
                writer.add_attachment(filename, file_data)
                embedded_count += 1
                logging.info(f"Successfully embedded: {filename}")
                
            except Exception as e:
                logging.error(f"Failed to embed {file.filename}: {str(e)}")
                return jsonify({"error": f"Failed to embed {file.filename}: {str(e)}"}), 500
        
        if embedded_count == 0:
            return jsonify({"error": "No files were successfully embedded"}), 500
        
        # Write to binary output
        output = BytesIO()
        writer.write(output)
        output.seek(0)
        
        logging.info(f"Successfully created PDF container with {embedded_count} embedded files")
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='embedded_container.pdf'
        )
        
    except Exception as e:
        logging.error(f"Embedding failed: {str(e)}", exc_info=True)
        return jsonify({"error": f"Embedding failed: {str(e)}"}), 500