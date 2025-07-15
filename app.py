#!/usr/bin/env python3
"""
Super minimal Flask app with no external dependencies
This will work even if requirements.txt is missing
"""

import os
import sys

# Use only Python standard library
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

class ResumeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Resume Categorizer - Railway Test</title>
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
            max-width: 600px;
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
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Resume Categorizer</h1>
        
        <div class="status">
            ✅ Railway Deployment Working!<br>
            🎯 No dependencies required
        </div>
        
        <p><strong>System Status:</strong></p>
        <div class="info">
            🐍 Python: ''' + sys.version.split()[0] + '''<br>
            🌐 Server: HTTP (built-in)<br>
            🚂 Railway: Connected<br>
            📦 Dependencies: None needed<br>
            🔧 Port: ''' + str(os.environ.get('PORT', '5000')) + '''
        </div>
        
        <a href="/health" class="btn">🏥 Health Check</a>
        <a href="/test" class="btn">🧪 Test API</a>
        
        <div style="margin-top: 30px; padding: 15px; background: #fff3cd; color: #856404; border-radius: 8px;">
            <strong>✅ Deployment Success!</strong><br>
            This proves Railway can deploy your Python app.<br>
            Next step: Add Flask and file processing.
        </div>
        
        <p style="margin-top: 20px; color: #666; font-size: 12px;">
            Using Python standard library only - no requirements.txt needed!
        </p>
    </div>
</body>
</html>'''
            self.wfile.write(html.encode())
            
        elif path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            
        elif path == '/test':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            data = {
                'status': 'working',
                'message': 'Resume Categorizer API - Standard Library Version',
                'python_version': sys.version.split()[0],
                'port': os.environ.get('PORT', '5000'),
                'environment': {
                    'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT', 'not_set'),
                    'PORT': os.environ.get('PORT', 'not_set'),
                },
                'dependencies': 'none_required',
                'next_steps': [
                    'Add requirements.txt with Flask',
                    'Upgrade to Flask-based app',
                    'Add document processing libraries'
                ]
            }
            
            self.wfile.write(json.dumps(data, indent=2).encode())
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>404 - Page Not Found</h1><p><a href="/">Go Home</a></p>')

    def log_message(self, format, *args):
        # Custom logging
        print(f"[{self.date_time_string()}] {format % args}")

def run_server():
    port = int(os.environ.get('PORT', 5000))
    
    print("🚀 Starting Resume Categorizer Server...")
    print(f"🌐 Port: {port}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"🔧 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"📄 Files in directory: {os.listdir('.')}")
    print("✅ No external dependencies required!")
    print(f"🌍 Server will be available at: http://0.0.0.0:{port}")
    
    server = HTTPServer(('0.0.0.0', port), ResumeHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.server_close()

if __name__ == '__main__':
    run_server()
