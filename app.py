from flask import Flask, request, render_template_string, jsonify, flash
from werkzeug.utils import secure_filename
import os
import tempfile
import traceback
import json
import time
from datetime import datetime
from query_pinecone import query_image_unique_addresses

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# File upload settings
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# HTML template for the interface
HTML_TEMPLATE = '''
<!doctype html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Recherche d'adresses par image - Paris 18</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Inter', Arial, sans-serif;
            color: #232946;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: #fff;
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            padding: 40px;
            max-width: 600px;
            width: 100%;
            text-align: center;
        }
        
        .title {
            color: #5b5be6;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 10px;
            letter-spacing: -0.5px;
        }
        
        .subtitle {
            color: #6b7280;
            font-size: 1.1rem;
            margin-bottom: 30px;
            font-weight: 400;
        }
        
        .upload-section {
            margin-bottom: 30px;
        }
        
        .upload-btn {
            background: #6c63ff;
            color: #fff;
            border: none;
            border-radius: 12px;
            padding: 16px 32px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 12px;
            box-shadow: 0 4px 15px rgba(108, 99, 255, 0.3);
        }
        
        .upload-btn:hover {
            background: #5b5be6;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(108, 99, 255, 0.4);
        }
        
        .upload-btn svg {
            width: 24px;
            height: 24px;
        }
        
        .file-input {
            display: none;
        }
        
        .results-section {
            margin-top: 30px;
        }
        
        .results-title {
            color: #5b5be6;
            font-weight: 700;
            font-size: 1.3rem;
            margin-bottom: 20px;
        }
        
        .result-item {
            background: #f8fafc;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            text-align: left;
            border-left: 4px solid #6c63ff;
            transition: all 0.3s ease;
        }
        
        .result-link {
            text-decoration: none;
            color: inherit;
            display: block;
        }
        
        .result-link:hover {
            text-decoration: none;
            color: inherit;
        }
        
        .result-item:hover {
            background: #f1f5f9;
            transform: translateX(5px);
            cursor: pointer;
        }
        
        .result-number {
            display: inline-block;
            background: #6c63ff;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            text-align: center;
            line-height: 30px;
            font-weight: 700;
            margin-right: 50px;
        }
        
        .result-address {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 8px;
        }
        
        .result-score {
            color: #6b7280;
            font-size: 0.9rem;
        }
        
        .result-maps {
            margin-top: 8px;
        }
        
        .maps-link {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: #3b82f6;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            padding: 4px 8px;
            border-radius: 6px;
            background: #eff6ff;
            transition: all 0.2s ease;
        }
        
        .maps-link:hover {
            background: #dbeafe;
            color: #1d4ed8;
            transform: translateY(-1px);
        }
        
        .maps-link svg {
            width: 14px;
            height: 14px;
        }
        
        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 16px;
            border-radius: 12px;
            margin: 20px 0;
            font-weight: 500;
            border-left: 4px solid #dc2626;
        }
        
        .success {
            background: #d1fae5;
            color: #065f46;
            padding: 16px;
            border-radius: 12px;
            margin: 20px 0;
            font-weight: 500;
            border-left: 4px solid #10b981;
        }
        
        .loader {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(255,255,255,0.95);
            z-index: 9999;
            justify-content: center;
            align-items: center;
            flex-direction: column;
        }
        
        .loader.active {
            display: flex;
        }
        
        .spinner {
            border: 6px solid #e3edfa;
            border-top: 6px solid #6c63ff;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loader-text {
            font-size: 1.1rem;
            color: #6c63ff;
            font-weight: 600;
            text-align: center;
        }
        
        .stats {
            background: #f8fafc;
            border-radius: 12px;
            padding: 20px;
            margin-top: 30px;
            text-align: center;
        }
        
        .stats-title {
            color: #5b5be6;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .stats-text {
            color: #6b7280;
            font-size: 0.9rem;
        }
        
        @media (max-width: 600px) {
            .container { padding: 20px; }
            .title { font-size: 1.5rem; }
            .upload-btn { padding: 14px 24px; font-size: 1rem; }
        }
    </style>
</head>
<body>
    <div class="loader" id="loader">
        <div class="spinner"></div>
        <div class="loader-text">Analyse de l'image par notre IA</div>
    </div>
    
    <div class="container">
        <div class="title">🔍 Recherche d'adresse par image</div>
        <div class="subtitle">Téléchargez une photo d'immeuble pour retrouver l'adresse. Disponible pour Paris 18</div>
        
        <div class="upload-section">
            <form id="upload-form" method="post" enctype="multipart/form-data">
                <input type="file" name="file" id="file-input" class="file-input" accept="image/*" required>
                <label for="file-input" class="upload-btn">
                    <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5-5m0 0l5 5m-5-5v12"/>
                    </svg>
                    Choisir une image
                </label>
            </form>
        </div>
        
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        
        {% if success %}
            <div class="success">{{ success }}</div>
        {% endif %}
        
        {% if results %}
            <div class="results-section">
                <div class="results-title">🏠 Adresses trouvées (5 plus similaires)</div>
                {% for result in results %}
                    <a href="{{ result.google_maps_url }}" target="_blank" class="result-link">
                        <div class="result-item">
                            <span class="result-number">{{ loop.index }}</span>
                            <div>
                                <div class="result-address">{{ result.address }}</div>
                                <div class="result-score">Score de confiance: {{ "%.2f"|format(result.score * 100) }}%</div>
                                <div class="result-maps">
                                    <span class="maps-link">
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                                        </svg>
                                        Voir sur Google Maps
                                    </span>
                                </div>
                            </div>
                        </div>
                    </a>
                {% endfor %}
            </div>
            
            <div class="stats">
                <div class="stats-text">
                    L'adresse n'est pas la bonne? Votre image doit avoir une résolution suffisamment bonne et peu d'éléments parasites au premier plan.
                </div>
            </div>
        {% endif %}
    </div>
    
    <script>
        const form = document.getElementById('upload-form');
        const fileInput = document.getElementById('file-input');
        const loader = document.getElementById('loader');
        
        form.addEventListener('submit', function() {
            loader.classList.add('active');
        });
        
        fileInput.addEventListener('change', function() {
            loader.classList.add('active');
            form.submit();
        });
        
        window.onload = function() {
            loader.classList.remove('active');
        };
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    results = None
    error = None
    success = None
    total_vectors = "636,145"  # From your Pinecone index info
    processing_time = None
    
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                error = "Aucun fichier sélectionné."
            else:
                file = request.files['file']
                if file.filename == '':
                    error = "Aucun fichier sélectionné."
                elif not allowed_file(file.filename):
                    error = "Format de fichier non supporté. Utilisez PNG, JPG, JPEG, BMP ou GIF."
                else:
                    # Save file temporarily
                    filename = secure_filename(file.filename)
                    temp_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(temp_path)
                    
                    try:
                        # Start timing
                        start_time = time.time()
                        
                        # Process image and get 5 unique addresses
                        results = query_image_unique_addresses(temp_path, top_k=5)
                        
                        # Calculate processing time
                        processing_time = round(time.time() - start_time, 2)
                        
                        if results:
                            success = f"Analyse terminée ! {len(results)} adresses uniques trouvées."
                        else:
                            error = "Aucune adresse similaire trouvée dans la base de données."
                            
                    except Exception as e:
                        error = f"Erreur lors du traitement de l'image: {str(e)}"
                        print("Error processing image:", str(e))
                        print(traceback.format_exc())
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                            
        except Exception as e:
            error = "Erreur lors du traitement de l'image."
            print("Error processing image:", str(e))
            print(traceback.format_exc())
    
    return render_template_string(HTML_TEMPLATE, 
                                results=results, 
                                error=error, 
                                success=success,
                                total_vectors=total_vectors,
                                processing_time=processing_time)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check if environment variables are available
        pinecone_api_key = os.environ.get('PINECONE_API_KEY')
        pinecone_env = os.environ.get('PINECONE_ENVIRONMENT')
        pinecone_index = os.environ.get('PINECONE_INDEX_NAME')
        
        return jsonify({
            'status': 'healthy', 
            'timestamp': datetime.utcnow().isoformat(),
            'pinecone_index': pinecone_index or 'paris-18',
            'total_vectors': 636145,
            'env_vars_available': {
                'PINECONE_API_KEY': bool(pinecone_api_key),
                'PINECONE_ENVIRONMENT': bool(pinecone_env),
                'PINECONE_INDEX_NAME': bool(pinecone_index)
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
