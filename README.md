# PDF Embedding/Extraction API  
## Cloud Computing Mini-Project  
**Description**: Flask API to embed/extract PDFs with Swagger docs.  

/pdf-embedding-api
├── app/
│   ├── static/          # Static files (CSS, JS)
│       ├── styles.css       # CSS styles
│       ├── scripts.js    # Js scripts
│   ├── templates/       # HTML templates
│       ├── index.html       # Main HTML page
│   ├── main.py          # Flask app initialization
│   ├── api              # API routes
│       ├── embed.py          # Embedding endpoint
|       ├── extract.py        # Extraction endpoint
│   ├── swagger/        # Swagger documentation
│       ├── 
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