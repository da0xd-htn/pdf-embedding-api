from flask import Flask, render_template
from app.api.embed import embed_bp  # Add this import

app = Flask(__name__)

# Register blueprint
app.register_blueprint(embed_bp)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)