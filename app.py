#!/usr/bin/env python3
"""
Minimal Flask app to test Nixpacks deployment
Use this first to ensure Railway deployment works
"""

import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resume Categorizer - Test</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: #f0f2f5; 
                text-align: center; 
                padding: 50px; 
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                max-width: 600px;
                margin: 0 auto;
            }
            h1 { color: #333; }
            .status { 
                background: #d4edda; 
                color: #155724; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 20px 0; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Resume Categorizer</h1>
            <div class="status">
                ✅ Nixpacks deployment successful!
            </div>
            <p>Railway domain detection working.</p>
            <p>Ready to deploy full application.</p>
            <p><a href="/test">Test endpoint</a> | <a href="/health">Health check</a></p>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return 'OK'

@app.route('/test')
def test():
    return jsonify({
        'status': 'working',
        'python_version': os.sys.version,
        'port': os.environ.get('PORT', '5000'),
        'railway_env': os.environ.get('RAILWAY_ENVIRONMENT', 'not_set')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
