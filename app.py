import os
import json
from flask import Flask, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import time # Import time for realistic file processing simulation

# Configuration
# This is the valid API key prefix required for the Bearer Token authentication.
VALID_API_KEY_PREFIX = "kaiiddo-ith"
# The new, professional, big valid token (32 hex characters plus prefix).
FULL_VALID_TOKEN = f"{VALID_API_KEY_PREFIX}-8b7c4a1e9f2d6g3h5j0k9l8m7n6p5q4r" 

# Set up the upload folder (In this demo, files are saved here and served via /share)
UPLOAD_FOLDER = 'uploaded_files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- ROUTES ---

@app.route('/')
def serve_landing_page():
    """Serves the main landing page (index.html)."""
    return send_from_directory('.', 'index.html')

@app.route('/docs')
def serve_api_docs_json():
    """Serves a JSON document detailing API usage examples and specifications."""
    docs_content = {
        "apiName": "Kaiiddo Cloud File Hosting API",
        "version": "1.0",
        "authentication": {
            "method": "Bearer Token",
            "requiredToken": FULL_VALID_TOKEN,
            "headerExample": "Authorization: Bearer " + FULL_VALID_TOKEN
        },
        "endpoints": [
            {
                "path": "/api/upload",
                "method": "POST",
                "description": "Upload a file to the Kaiiddo Cloud. Requires authentication and a file.",
                "requestBody": {
                    "contentType": "multipart/form-data",
                    "fields": [
                        {"name": "file", "type": "file", "required": True, "notes": "The file to be uploaded."}
                    ]
                },
                "successResponse": {
                    "ok": True,
                    "sharedLink": "https://<your-domain>/share/<unique_id>/<filename>",
                    "fileName": "example.jpg",
                    "fileSize": "1048576",
                    "uploadDate": "2025-11-22T12:05:00.000Z"
                },
                "errorResponses": [
                    {"errorCode": 401, "errorMessage": "Authentication required. Missing Authorization header."},
                    {"errorCode": 403, "errorMessage": "Invalid Bearer Token."},
                    {"errorCode": 400, "errorMessage": "No file part in the request body."}
                ]
            }
        ],
        "notes": "Files are permanently hosted by the Flask server in the UPLOAD_FOLDER and accessible via the provided sharedLink (/share/ route)."
    }
    return jsonify(docs_content)

@app.route('/api/upload', methods=['POST'])
def api_upload_file():
    """
    Handles file upload requests, requiring a Bearer Token for authentication.
    Method: POST
    Authentication: Bearer Token (must match FULL_VALID_TOKEN)
    """
    # 1. API Bearer Token Authentication Check
    auth_header = request.headers.get('Authorization')
    
    # Simulating a small delay for realistic processing time
    time.sleep(0.5) 
    
    if not auth_header:
        # 401 Unauthorized - No authorization header
        return jsonify({
            "ok": False,
            "errorCode": 401,
            "errorMessage": "Authentication required. Missing Authorization header."
        }), 401

    try:
        scheme, token = auth_header.split()
    except ValueError:
        # 401 Unauthorized - Invalid header format
        return jsonify({
            "ok": False,
            "errorCode": 401,
            "errorMessage": "Invalid Authorization header format. Must be 'Bearer [token]'."
        }), 401

    if scheme.lower() != 'bearer' or token != FULL_VALID_TOKEN:
        # 403 Forbidden - Invalid token
        return jsonify({
            "ok": False,
            "errorCode": 403,
            "errorMessage": f"Invalid Bearer Token. Token must match: {FULL_VALID_TOKEN}"
        }), 403

    # 2. File Check
    if 'file' not in request.files:
        # 400 Bad Request - File missing in request
        return jsonify({
            "ok": False,
            "errorCode": 400,
            "errorMessage": "No file part in the request body."
        }), 400

    file = request.files['file']
    
    if file.filename == '':
        # 400 Bad Request - No selected file
        return jsonify({
            "ok": False,
            "errorCode": 400,
            "errorMessage": "No selected file for upload."
        }), 400

    if file:
        # 3. Handle File Storage (Files are hosted on the Koyeb persistent storage)
        filename = secure_filename(file.filename)
        unique_id = uuid.uuid4().hex[:12] 
        # Files are stored with a unique ID prefix to ensure uniqueness and simple lookup
        storage_filename = f"{unique_id}-{filename}"
        
        # This saves the file to the UPLOAD_FOLDER
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], storage_filename))
        
        # 4. Generate Success Response with Shared Link
        # The shared link points to the /share route, which serves the file directly
        mock_shared_link = f"{request.url_root}share/{unique_id}/{filename}"
        
        return jsonify({
            "ok": True,
            "sharedLink": mock_shared_link,
            "fileName": filename,
            "fileSize": file.content_length if hasattr(file, 'content_length') else 'Unknown',
            "uploadDate": datetime.now().isoformat()
        }), 200

# Route to serve the shared content (the actual hosted file)
@app.route('/share/<file_id>/<filename>')
def serve_shared_file(file_id, filename):
    """
    Serves the actual hosted file. 
    The browser will open/download the image, video, or document directly.
    """
    try:
        # Reconstruct the filename saved in the UPLOAD_FOLDER
        return send_from_directory(app.config['UPLOAD_FOLDER'], f'{file_id}-{filename}')
    except Exception:
        # File not found
        return f"<h1>404 Not Found</h1><p>The file associated with ID <code>{file_id}</code> and filename <code>{filename}</code> could not be located on the Kaiiddo Cloud server.</p>", 404

if __name__ == '__main__':
    app.run(debug=True, port=8000)
