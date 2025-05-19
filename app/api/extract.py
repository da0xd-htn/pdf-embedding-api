from flask import Blueprint, request, send_file, jsonify
from io import BytesIO
from PyPDF2 import PdfReader
from flasgger import swag_from

extract_bp = Blueprint('extract', __name__)

@extract_bp.route('/extract', methods=['POST'])
@swag_from({
    'tags': ['PDF'],
    'description': 'Extract embedded PDFs',
    'consumes': ['multipart/form-data'],
    'parameters': [
        {
            'name': 'pdf_file',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': 'PDF with embedded files'
        }
    ],
    'responses': {
        200: {
            'description': 'ZIP file containing extracted PDFs',
            'content': {'application/zip': {}}
        },
        400: {'description': 'Invalid input'}
    }
})
def extract_pdfs():
    if 'pdf_file' not in request.files:
        return {"error": "PDF file required"}, 400
        
    try:
        pdf = request.files['pdf_file']
        reader = PdfReader(pdf)
        
        if not hasattr(reader, 'attachments') or not reader.attachments:
            return {"error": "No embedded files found"}, 400
            
        # Create zip of attachments
        from zipfile import ZipFile
        output = BytesIO()
        
        with ZipFile(output, 'w') as zipf:
            for name, data in reader.attachments:
                if name.lower().endswith('.pdf'):
                    zipf.writestr(name, data)
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/zip',
            as_attachment=True,
            download_name='extracted_files.zip'
        )
    except Exception as e:
        return {"error": str(e)}, 500