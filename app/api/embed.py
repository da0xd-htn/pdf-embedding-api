from flask import Blueprint, request, send_file, jsonify
from flasgger.utils import swag_from
from PyPDF2 import PdfWriter
from PyPDF2.generic import (
    DictionaryObject,
    NameObject,
    ArrayObject,
    DecodedStreamObject,
    create_string_object,
)
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
        embedded_files = ArrayObject()  # Array to hold embedded files
        
        # Process each PDF file
        for file in valid_files:
            try:
                # Read file data
                file_data = file.read()
                
                # Validate PDF format
                if not file_data.startswith(b'%PDF'):
                    return jsonify({"error": f"File {file.filename} is not a valid PDF"}), 400
                
                # Create file stream object
                file_stream = DecodedStreamObject()
                file_stream.set_data(file_data)
                file_stream.update({NameObject("/Type"): NameObject("/EmbeddedFile")})
                file_stream_ref = writer._add_object(file_stream)
                
                # Create embedded file dictionary
                ef_dict = DictionaryObject({NameObject("/F"): file_stream_ref})
                file_spec = DictionaryObject({
                    NameObject("/Type"): NameObject("/Filespec"),
                    NameObject("/F"): create_string_object(file.filename),
                    NameObject("/EF"): ef_dict,
                })
                file_spec_ref = writer._add_object(file_spec)
                
                # Add to embedded files array (name, reference pairs)
                embedded_files.append(create_string_object(file.filename))
                embedded_files.append(file_spec_ref)
                
                logging.info(f"Successfully embedded: {file.filename}")
                
            except Exception as e:
                logging.error(f"Failed to embed {file.filename}: {str(e)}")
                return jsonify({"error": f"Failed to embed {file.filename}: {str(e)}"}), 500
        
        # Create embedded files tree structure
        embedded_files_tree = DictionaryObject({NameObject("/Names"): embedded_files})
        
        # Update root object with embedded files
        writer._root_object.update({
            NameObject("/Names"): writer._add_object(DictionaryObject({
                NameObject("/EmbeddedFiles"): writer._add_object(embedded_files_tree)
            }))
        })
        
        # Write to binary output
        output = BytesIO()
        writer.write(output)
        output.seek(0)
        
        logging.info(f"Successfully created PDF container with {len(valid_files)} embedded files")
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='embedded_container.pdf'
        )
        
    except Exception as e:
        logging.error(f"Embedding failed: {str(e)}", exc_info=True)
        return jsonify({"error": f"Embedding failed: {str(e)}"}), 500