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
        
        # Extract embedded files using direct PDF structure navigation
        embedded_files = {}
        
        try:
            # Navigate PDF structure: Root -> Names -> EmbeddedFiles
            catalog = reader.trailer["/Root"]
            
            if "/Names" not in catalog:
                return jsonify({"error": "No embedded files found - missing /Names in catalog"}), 404
            
            names = catalog["/Names"]
            if "/EmbeddedFiles" not in names:
                return jsonify({"error": "No embedded files found - missing /EmbeddedFiles"}), 404
            
            files_dict = names["/EmbeddedFiles"]
            if "/Names" not in files_dict:
                return jsonify({"error": "No embedded files found - missing /Names array"}), 404
            
            names_array = files_dict["/Names"]
            logging.info(f"Found names array with {len(names_array)} items")
            
            # Process embedded files in pairs (name, file_spec)
            for i in range(0, len(names_array), 2):
                if i + 1 >= len(names_array):
                    break
                    
                try:
                    # Get filename and file specification
                    filename = names_array[i]
                    file_spec = names_array[i + 1].get_object()
                    
                    # Navigate to the actual file data
                    if "/EF" in file_spec and "/F" in file_spec["/EF"]:
                        file_stream = file_spec["/EF"]["/F"].get_object()
                        file_data = file_stream.get_data()
                        
                        if file_data and len(file_data) > 0:
                            embedded_files[filename] = file_data
                            logging.info(f"Extracted: {filename} ({len(file_data)} bytes)")
                        else:
                            logging.warning(f"Empty data for file: {filename}")
                    else:
                        logging.warning(f"Invalid file structure for: {filename}")
                        
                except Exception as e:
                    logging.error(f"Failed to extract file at index {i}: {str(e)}")
                    continue
            
        except KeyError as e:
            logging.error(f"PDF structure navigation failed: {str(e)}")
            return jsonify({"error": f"Invalid PDF structure: missing {str(e)}"}), 400
        except Exception as e:
            logging.error(f"Extraction failed: {str(e)}")
            return jsonify({"error": f"Extraction failed: {str(e)}"}), 500
        
        if not embedded_files:
            return jsonify({"error": "No embedded files found"}), 404
        
        logging.info(f"Total files extracted: {len(embedded_files)}")
        
        # Create ZIP file with extracted PDFs
        zip_buffer = BytesIO()
        extracted_count = 0
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, content in embedded_files.items():
                try:
                    # Clean filename
                    safe_filename = str(filename).strip()
                    if not safe_filename.lower().endswith('.pdf'):
                        safe_filename = f"{safe_filename}.pdf"
                    
                    # Validate that extracted data is actually a PDF
                    if isinstance(content, bytes) and len(content) > 4 and content.startswith(b'%PDF'):
                        zipf.writestr(safe_filename, content)
                        extracted_count += 1
                        logging.info(f"Added to ZIP: {safe_filename} ({len(content)} bytes)")
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