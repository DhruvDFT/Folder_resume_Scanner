#!/usr/bin/env python3
"""
Minimal Resume Categorizer - Railway Test
Start with this basic version to ensure deployment works
"""

import os
from flask import Flask, request, render_template_string, jsonify, redirect, flash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'test-secret-key')

@app.route('/')
def home():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Resume Categorizer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }
        .container {
            background: rgba(255, 255, 255, 0.95);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 500px;
        }
        h1 { color: #2d3748; margin-bottom: 20px; }
        .status {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            text-decoration: none;
            display: inline-block;
            margin: 10px;
        }
        .info { 
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📁 Resume Categorizer</h1>
        
        <div class="status">
            ✅ Railway Deployment Successful!
        </div>
        
        <p>Web-based resume categorization system</p>
        
        <div class="info">
            <strong>System Status:</strong><br>
            🐍 Python: Working<br>
            🌐 Flask: Working<br>
            🚂 Railway: Connected<br>
            📦 Nixpacks: Success
        </div>
        
        <a href="/test" class="btn">🧪 Test API</a>
        <a href="/upload" class="btn">📤 Upload Test</a>
        
        <p style="margin-top: 30px; color: #666; font-size: 14px;">
            Ready to process resume files!<br>
            This minimal version confirms deployment works.
        </p>
    </div>
</body>
</html>'''

@app.route('/health')
def health():
    return 'OK'

@app.route('/test')
def test():
    return jsonify({
        'status': 'working',
        'message': 'Resume Categorizer API is running',
        'python_version': os.sys.version.split()[0],
        'port': os.environ.get('PORT', '5000'),
        'environment': {
            'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT'),
            'PORT': os.environ.get('PORT'),
            'SECRET_KEY': 'configured' if os.environ.get('SECRET_KEY') else 'default'
        }
    })

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        return jsonify({
            'message': 'Upload endpoint working',
            'files_received': len(request.files),
            'next_step': 'Add document processing libraries'
        })
    
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Upload Test</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; background: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        input[type="file"] { width: 100%; padding: 10px; margin: 10px 0; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📤 Upload Test</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="files" multiple accept=".pdf,.docx,.txt">
            <button type="submit">Test Upload</button>
        </form>
        <p><a href="/">← Back to Home</a></p>
    </div>
</body>
</html>'''

if __name__ == '__main__':
    print("🚀 Starting Resume Categorizer...")
    print(f"🌐 Port: {os.environ.get('PORT', 5000)}")
    print(f"🔧 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
