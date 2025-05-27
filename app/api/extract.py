from flask import Blueprint, request, send_file, jsonify
from flasgger.utils import swag_from
from PyPDF2 import PdfReader
from io import BytesIO
import zipfile
import logging

extract_bp = Blueprint('extract', __name__)

@extract_bp.route('/extract_embedded_pdf', methods=['POST'])
@swag_from({
    'tags': ['PDF Operations'],
    'summary': 'Extract embedded PDFs from a PDF container',
    'description': 'Extracts all PDF files that were embedded in a PDF container and returns them as a ZIP file',
    'consumes': ['multipart/form-data'],
    'parameters': [{
        'name': 'pdf_file',
        'in': 'formData',
        'type': 'file',
        'required': True,
        'description': 'PDF container file containing embedded PDFs'
    }],
    'responses': {
        200: {
            'description': 'ZIP file containing extracted PDF files',
            'schema': {
                'type': 'file'
            }
        },
        400: {
            'description': 'Bad request - no file uploaded or invalid file',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'No embedded files found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Server error during extraction',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def extract_pdfs():
    """
    Extract all embedded PDF files from a PDF container
    """
    try:
        if 'pdf_file' not in request.files:
            return jsonify({"error": "PDF file is required"}), 400
        
        pdf_file = request.files['pdf_file']
        if not pdf_file or pdf_file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Read PDF as binary data
        pdf_data = pdf_file.read()
        
        # Validate PDF format
        if not pdf_data.startswith(b'%PDF'):
            return jsonify({"error": "Uploaded file is not a valid PDF"}), 400
        
        reader = PdfReader(BytesIO(pdf_data))
        logging.info(f"Successfully loaded PDF with {len(reader.pages)} pages")
        
        # Extract embedded files - simplified approach
        attachments = []
        
        try:
            # Use PyPDF2's built-in method to get embedded files
            if hasattr(reader, 'attachments') and reader.attachments:
                logging.info(f"Found {len(reader.attachments)} attachments using .attachments")
                for filename, data in reader.attachments.items():
                    if data and len(data) > 0:
                        attachments.append((filename, data))
                        logging.info(f"Extracted: {filename} ({len(data)} bytes)")
            
            # Alternative method using embedded_files attribute
            elif hasattr(reader, 'embedded_files') and reader.embedded_files:
                logging.info(f"Found {len(reader.embedded_files)} embedded files")
                for filename, file_data in reader.embedded_files.items():
                    try:
                        # Handle different data formats
                        if isinstance(file_data, tuple) and len(file_data) >= 2:
                            # Extract from tuple format (filename, file_object)
                            file_obj = file_data[1]
                            if hasattr(file_obj, 'get_data'):
                                data = file_obj.get_data()
                            elif hasattr(file_obj, 'data'):
                                data = file_obj.data
                            else:
                                data = file_obj
                        elif hasattr(file_data, 'get_data'):
                            data = file_data.get_data()
                        elif hasattr(file_data, 'data'):
                            data = file_data.data
                        else:
                            data = file_data
                        
                        if data and len(data) > 0:
                            attachments.append((filename, data))
                            logging.info(f"Extracted: {filename} ({len(data)} bytes)")
                    except Exception as e:
                        logging.warning(f"Failed to extract {filename}: {str(e)}")
                        continue
            
            else:
                # Manual extraction method as fallback
                logging.info("Using manual extraction method")
                if '/Root' in reader.trailer:
                    root = reader.trailer['/Root']
                    if '/Names' in root and '/EmbeddedFiles' in root['/Names']:
                        embedded_files = root['/Names']['/EmbeddedFiles']
                        if '/Names' in embedded_files:
                            names_array = embedded_files['/Names']
                            
                            # Process pairs of (filename, filespec)
                            for i in range(0, len(names_array), 2):
                                if i + 1 < len(names_array):
                                    try:
                                        filename = str(names_array[i]).strip('()')
                                        filespec = names_array[i + 1]
                                        
                                        # Get the actual file data
                                        if hasattr(filespec, 'get_object'):
                                            filespec = filespec.get_object()
                                        
                                        if '/EF' in filespec and '/F' in filespec['/EF']:
                                            file_stream = filespec['/EF']['/F']
                                            if hasattr(file_stream, 'get_data'):
                                                data = file_stream.get_data()
                                                if data and len(data) > 0:
                                                    attachments.append((filename, data))
                                                    logging.info(f"Manually extracted: {filename} ({len(data)} bytes)")
                                    except Exception as e:
                                        logging.warning(f"Manual extraction failed for file {i//2}: {str(e)}")
                                        continue
        
        except Exception as e:
            logging.error(f"Extraction process failed: {str(e)}")
        
        if not attachments:
            return jsonify({"error": "No embedded files found in the PDF"}), 404
        
        logging.info(f"Total files to extract: {len(attachments)}")
        
        # Create ZIP file with extracted PDFs
        zip_buffer = BytesIO()
        extracted_count = 0
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, data in attachments:
                try:
                    # Clean filename
                    safe_filename = str(filename).strip()
                    if not safe_filename.lower().endswith('.pdf'):
                        safe_filename = f"{safe_filename}.pdf"
                    
                    # Validate that extracted data is actually a PDF
                    if isinstance(data, bytes) and len(data) > 4 and data.startswith(b'%PDF'):
                        zipf.writestr(safe_filename, data)
                        extracted_count += 1
                        logging.info(f"Added to ZIP: {safe_filename} ({len(data)} bytes)")
                    else:
                        logging.warning(f"Skipped invalid PDF data for {filename}")
                        
                except Exception as e:
                    logging.error(f"Failed to add {filename} to ZIP: {str(e)}")
                    continue
        
        if extracted_count == 0:
            return jsonify({"error": "No valid PDF files could be extracted"}), 404
        
        zip_buffer.seek(0)
        
        logging.info(f"Successfully created ZIP with {extracted_count} PDF files")
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='extracted_pdfs.zip'
        )
        
    except Exception as e:
        logging.error(f"Extraction failed: {str(e)}", exc_info=True)
        return jsonify({"error": f"Extraction failed: {str(e)}"}), 500