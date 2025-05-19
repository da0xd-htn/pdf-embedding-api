# PDF Embedding/Extraction API  
## Cloud Computing Mini-Project  
**Description**: Flask API to embed/extract PDFs with Swagger docs.  

/pdf-embedding-api
├── app/
│   ├── static/          # Static files (CSS, JS)
│       ├── styles.css       # CSS styles
│   ├── templates/       # HTML templates
│       ├── index.html       # Main HTML page
│   ├── main.py          # Flask app initialization
│   ├── api              # API routes
│       ├── embed.py          # Embedding endpoint
|       ├── extract.py        # Extraction endpoint
│   ├── swagger/        # Swagger documentation
│       ├── swagger.json      # Swagger JSON file
├── requirements.txt
├── .gitignore
├── redame.md




### Technologies  
- Python 3.9  
- Flask  
- PyPDF2  
- Docker  
- Azure  

## Setup  
```bash
git clone https://github.com/yourusername/pdf-embedding-api.git
cd pdf-embedding-api
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt