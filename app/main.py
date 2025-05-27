
from flask import Flask, render_template
from flasgger import Swagger
from app.api.embed import embed_bp
from app.api.extract import extract_bp

app = Flask(__name__)

# Configure Swagger
app.config['SWAGGER'] = {
    'title': 'PDF Embedding API',
    'uiversion': 3,
    'specs_route': '/apidocs/'
}
Swagger(app)

# Register blueprints
app.register_blueprint(embed_bp, url_prefix='/api')
app.register_blueprint(extract_bp, url_prefix='/api')

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)