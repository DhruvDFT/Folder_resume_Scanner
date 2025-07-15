#!/usr/bin/env python3
"""
Web-based Resume Categorizer for Railway Deployment
Upload resumes through web interface and get categorized results
"""

import os
import re
import zipfile
import tempfile
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import uuid

from flask import Flask, request, render_template_string, jsonify, send_file, session, redirect, flash
from werkzeug.utils import secure_filename

# Try to import document processing libraries
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'resume-categorizer-secret-2024')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Configuration
UPLOAD_FOLDER = '/tmp/uploads'
PROCESSED_FOLDER = '/tmp/processed'
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

class ResumeCategorizer:
    def __init__(self):
        self.domain_keywords = {
            'Software_Engineering': [
                'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js', 'django', 
                'flask', 'spring boot', 'full stack', 'frontend', 'backend', 'web developer',
                'software engineer', 'developer', 'programming', 'coding', 'software development',
                'html', 'css', 'sql', 'database', 'api', 'rest', 'microservices', 'agile',
                'git', 'github', 'mvc', 'orm', 'json', 'xml', 'mobile app', 'ios', 'android'
            ],
            'Data_Science': [
                'data scientist', 'machine learning', 'deep learning', 'tensorflow', 'pytorch',
                'pandas', 'numpy', 'matplotlib', 'sql', 'tableau', 'power bi', 'statistics',
                'data analyst', 'analytics', 'big data', 'hadoop', 'spark', 'r programming',
                'data mining', 'predictive modeling', 'data visualization', 'scikit-learn',
                'neural network', 'artificial intelligence', 'nlp', 'computer vision'
            ],
            'VLSI_Electronics': [
                'vlsi', 'verilog', 'vhdl', 'fpga', 'asic', 'system verilog', 'cadence', 'synopsys',
                'xilinx', 'altera', 'rtl design', 'verification', 'physical design', 'analog design',
                'digital design', 'semiconductor', 'chip design', 'circuit design', 'embedded',
                'microcontroller', 'arm', 'risc', 'dft', 'timing analysis', 'layout'
            ],
            'DevOps_Cloud': [
                'devops', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform',
                'ansible', 'linux', 'ci/cd', 'cloud engineer', 'infrastructure', 'deployment',
                'monitoring', 'automation', 'scripting', 'cloud computing', 'containerization',
                'puppet', 'chef', 'nagios', 'prometheus', 'grafana', 'elk stack'
            ],
            'Mechanical_Engineering': [
                'mechanical engineer', 'cad', 'solidworks', 'autocad', 'catia', 'ansys',
                'manufacturing', 'design engineer', 'product design', 'mechanical design',
                'thermal analysis', 'fea', 'prototype', 'quality control', 'lean manufacturing',
                'pro/engineer', 'inventor', 'nx', 'creo', 'matlab', 'simulink'
            ],
            'Civil_Engineering': [
                'civil engineer', 'construction', 'structural design', 'project management',
                'autocad', 'revit', 'surveying', 'site engineer', 'concrete', 'steel design',
                'infrastructure', 'transportation', 'water resources', 'geotechnical',
                'etabs', 'sap2000', 'staad pro', 'primavera', 'ms project'
            ]
        }
        
        self.experience_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+)\+?\s*yrs?',
            r'(\d+)\+?\s*year\s*exp',
            r'experience\s*:?\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*in',
            r'(\d+)\+?\s*years?\s*working'
        ]

    def extract_text_from_pdf(self, file_path):
        """Extract text from PDF file"""
        if not PDF_AVAILABLE:
            return ""
        
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")
            return ""

    def extract_text_from_docx(self, file_path):
        """Extract text from Word document"""
        if not DOCX_AVAILABLE:
            return ""
        
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"Error reading DOCX {file_path}: {e}")
            return ""

    def extract_text_from_file(self, file_path):
        """Extract text from various file formats"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            return self.extract_text_from_docx(file_path)
        elif file_ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            except:
                try:
                    with open(file_path, 'r', encoding='latin-1') as file:
                        return file.read()
                except Exception as e:
                    print(f"Error reading TXT {file_path}: {e}")
                    return ""
        else:
            return Path(file_path).stem

    def categorize_domain(self, text_content):
        """Categorize resume by domain based on keywords"""
        domain_scores = {}
        text_lower = text_content.lower()
        
        for domain, keywords in self.domain_keywords.items():
            score = 0
            for keyword in keywords:
                score += text_lower.count(keyword.lower())
            
            if score > 0:
                domain_scores[domain] = score
        
        if not domain_scores:
            return 'Other'
        
        return max(domain_scores.keys(), key=lambda x: domain_scores[x])

    def categorize_experience(self, text_content):
        """Categorize by experience level"""
        text_lower = text_content.lower()
        max_years = 0
        
        for pattern in self.experience_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    years = int(match)
                    if 0 <= years <= 50:
                        max_years = max(max_years, years)
                except:
                    continue
        
        if max_years == 0:
            return 'Fresher_0-1_years'
        elif max_years <= 3:
            return 'Junior_1-3_years' 
        elif max_years <= 6:
            return 'Mid_Level_3-6_years'
        else:
            return 'Senior_6plus_years'

# Global categorizer instance
categorizer = ResumeCategorizer()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

def create_zip_file(categorized_files, session_id):
    """Create a zip file with categorized resumes"""
    zip_path = os.path.join(PROCESSED_FOLDER, f'categorized_resumes_{session_id}.zip')
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for category_info in categorized_files:
            file_path = category_info['file_path']
            domain = category_info['domain']
            experience = category_info['experience']
            original_name = category_info['original_name']
            
            # Create folder structure in zip
            zip_file_path = f"{domain}/{experience}/{original_name}"
            zipf.write(file_path, zip_file_path)
    
    return zip_path

@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads and categorization"""
    if 'files' not in request.files:
        flash('No files selected')
        return redirect('/')
    
    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        flash('No files selected')
        return redirect('/')
    
    # Create session ID for this upload
    session_id = str(uuid.uuid4())[:8]
    session['session_id'] = session_id
    
    # Process files
    categorized_files = []
    stats = defaultdict(lambda: defaultdict(int))
    processed_count = 0
    failed_count = 0
    
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            try:
                # Save uploaded file
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_{filename}")
                file.save(file_path)
                
                # Extract text and categorize
                text_content = categorizer.extract_text_from_file(file_path)
                if not text_content.strip():
                    text_content = filename  # Fallback to filename
                
                domain = categorizer.categorize_domain(text_content)
                experience = categorizer.categorize_experience(text_content)
                
                categorized_files.append({
                    'original_name': filename,
                    'file_path': file_path,
                    'domain': domain,
                    'experience': experience,
                    'text_preview': text_content[:200] + '...' if len(text_content) > 200 else text_content
                })
                
                stats[domain][experience] += 1
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing {file.filename}: {e}")
                failed_count += 1
        else:
            failed_count += 1
    
    if not categorized_files:
        flash('No valid files were processed')
        return redirect('/')
    
    # Create zip file
    try:
        zip_path = create_zip_file(categorized_files, session_id)
        session['zip_path'] = zip_path
    except Exception as e:
        print(f"Error creating zip: {e}")
        flash('Error creating download file')
        return redirect('/')
    
    # Store results in session
    session['categorized_files'] = categorized_files
    session['stats'] = dict(stats)
    session['processed_count'] = processed_count
    session['failed_count'] = failed_count
    
    return redirect('/results')

@app.route('/results')
def show_results():
    """Display categorization results"""
    if 'categorized_files' not in session:
        flash('No results to display')
        return redirect('/')
    
    return render_template_string(RESULTS_TEMPLATE, 
                                categorized_files=session['categorized_files'],
                                stats=session['stats'],
                                processed_count=session['processed_count'],
                                failed_count=session['failed_count'])

@app.route('/download')
def download_zip():
    """Download categorized resumes as zip file"""
    if 'zip_path' not in session:
        flash('No download available')
        return redirect('/')
    
    zip_path = session['zip_path']
    if not os.path.exists(zip_path):
        flash('Download file not found')
        return redirect('/')
    
    return send_file(zip_path, 
                    as_attachment=True, 
                    download_name=f'categorized_resumes_{session["session_id"]}.zip',
                    mimetype='application/zip')

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    return jsonify({
        'status': 'online',
        'pdf_support': PDF_AVAILABLE,
        'docx_support': DOCX_AVAILABLE,
        'supported_formats': ['.pdf', '.docx', '.doc', '.txt'],
        'max_file_size': '50MB',
        'categories': {
            'domains': list(categorizer.domain_keywords.keys()) + ['Other'],
            'experience_levels': ['Fresher_0-1_years', 'Junior_1-3_years', 'Mid_Level_3-6_years', 'Senior_6plus_years']
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return 'OK'

# HTML Templates
HOME_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Resume Categorizer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .logo {
            width: 80px;
            height: 80px;
            margin: 0 auto 20px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            color: white;
        }
        h1 {
            color: #2d3748;
            margin-bottom: 10px;
            font-size: 32px;
        }
        .subtitle {
            color: #64748b;
            font-size: 18px;
            margin-bottom: 30px;
        }
        .upload-area {
            border: 3px dashed #cbd5e0;
            border-radius: 16px;
            padding: 60px 20px;
            text-align: center;
            background: #f8fafc;
            transition: all 0.3s ease;
            cursor: pointer;
            margin-bottom: 30px;
        }
        .upload-area:hover {
            border-color: #667eea;
            background: #edf2f7;
        }
        .upload-area.dragover {
            border-color: #667eea;
            background: #e6fffa;
        }
        .upload-icon {
            font-size: 48px;
            color: #a0aec0;
            margin-bottom: 20px;
        }
        .upload-text {
            color: #4a5568;
            font-size: 18px;
            margin-bottom: 10px;
        }
        .upload-subtext {
            color: #718096;
            font-size: 14px;
        }
        .file-input {
            display: none;
        }
        .selected-files {
            margin: 20px 0;
            padding: 20px;
            background: #f0f4f8;
            border-radius: 12px;
            display: none;
        }
        .file-list {
            list-style: none;
        }
        .file-item {
            padding: 8px 0;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 16px 32px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 40px;
        }
        .feature {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #f8fafc, #edf2f7);
            border-radius: 12px;
        }
        .feature-icon {
            font-size: 32px;
            margin-bottom: 10px;
            color: #667eea;
        }
        .feature h3 {
            color: #2d3748;
            margin-bottom: 8px;
            font-size: 16px;
        }
        .feature p {
            color: #64748b;
            font-size: 14px;
        }
        .status {
            background: #e6fffa;
            border: 1px solid #81e6d9;
            color: #234e52;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .flash-messages {
            margin-bottom: 20px;
        }
        .flash-message {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .flash-error {
            background: #fed7d7;
            color: #c53030;
            border: 1px solid #feb2b2;
        }
        @media (max-width: 600px) {
            .container { padding: 20px; }
            h1 { font-size: 24px; }
            .upload-area { padding: 40px 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">📁</div>
            <h1>Resume Categorizer</h1>
            <p class="subtitle">Automatically organize resumes by domain and experience level</p>
        </div>
        
        <div class="status">
            ✅ <strong>System Status:</strong> 
            PDF Support: {{ '✅' if ''' + str(PDF_AVAILABLE) + ''' else '❌' }} | 
            Word Support: {{ '✅' if ''' + str(DOCX_AVAILABLE) + ''' else '❌' }} | 
            Max File Size: 50MB
        </div>

        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <div class="flash-messages">
                    {% for message in messages %}
                        <div class="flash-message flash-error">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data">
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">📄</div>
                <div class="upload-text">Click to select resume files</div>
                <div class="upload-subtext">or drag and drop files here</div>
                <div class="upload-subtext" style="margin-top: 10px;">
                    Supported: PDF, DOCX, DOC, TXT • Max 50MB per file
                </div>
                <input type="file" id="fileInput" name="files" multiple accept=".pdf,.docx,.doc,.txt" class="file-input">
            </div>
            
            <div class="selected-files" id="selectedFiles">
                <h3>Selected Files:</h3>
                <ul class="file-list" id="fileList"></ul>
            </div>
            
            <button type="submit" class="btn" id="uploadBtn" disabled>
                🚀 Categorize Resumes
            </button>
        </form>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">🎯</div>
                <h3>Smart Categorization</h3>
                <p>Automatically sorts by 6+ domains</p>
            </div>
            <div class="feature">
                <div class="feature-icon">💼</div>
                <h3>Experience Levels</h3>
                <p>Groups by Fresher, Junior, Mid, Senior</p>
            </div>
            <div class="feature">
                <div class="feature-icon">📦</div>
                <h3>Organized Download</h3>
                <p>Get structured ZIP file output</p>
            </div>
            <div class="feature">
                <div class="feature-icon">⚡</div>
                <h3>Fast Processing</h3>
                <p>Bulk process multiple files</p>
            </div>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        const selectedFiles = document.getElementById('selectedFiles');
        const fileList = document.getElementById('fileList');

        // Click to select files
        uploadArea.addEventListener('click', () => fileInput.click());

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = Array.from(e.dataTransfer.files);
            const validFiles = files.filter(file => {
                const ext = file.name.toLowerCase();
                return ext.endsWith('.pdf') || ext.endsWith('.docx') || 
                       ext.endsWith('.doc') || ext.endsWith('.txt');
            });
            
            if (validFiles.length > 0) {
                fileInput.files = e.dataTransfer.files;
                updateFileList(validFiles);
            }
        });

        // File selection change
        fileInput.addEventListener('change', (e) => {
            updateFileList(Array.from(e.target.files));
        });

        function updateFileList(files) {
            fileList.innerHTML = '';
            
            if (files.length > 0) {
                selectedFiles.style.display = 'block';
                uploadBtn.disabled = false;
                
                files.forEach((file, index) => {
                    const li = document.createElement('li');
                    li.className = 'file-item';
                    li.innerHTML = `
                        <span>📄 ${file.name}</span>
                        <span>${(file.size / 1024 / 1024).toFixed(2)} MB</span>
                    `;
                    fileList.appendChild(li);
                });
            } else {
                selectedFiles.style.display = 'none';
                uploadBtn.disabled = true;
            }
        }

        // Form submission
        document.getElementById('uploadForm').addEventListener('submit', function() {
            uploadBtn.innerHTML = '⏳ Processing...';
            uploadBtn.disabled = true;
        });
    </script>
</body>
</html>
'''

RESULTS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Categorization Results</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        h1 {
            color: #2d3748;
            margin-bottom: 20px;
            font-size: 32px;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat {
            background: linear-gradient(135deg, #f8fafc, #edf2f7);
            padding: 25px;
            border-radius: 12px;
            text-align: center;
        }
        .stat-num {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 8px;
        }
        .stat-label {
            color: #64748b;
            font-size: 14px;
            font-weight: 600;
        }
        .download-section {
            background: linear-gradient(135deg, #e6fffa, #b2f5ea);
            border: 2px solid #4fd1c7;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 40px;
            text-align: center;
        }
        .btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 16px 32px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            margin: 8px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        .btn-secondary {
            background: linear-gradient(135deg, #718096, #4a5568);
        }
        .categories {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .category {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .category h3 {
            color: #2d3748;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }
        .experience-group {
            margin: 10px 0;
            padding: 10px;
            background: #f8fafc;
            border-radius: 8px;
        }
        .experience-title {
            font-weight: 600;
            color: #4a5568;
            margin-bottom: 5px;
        }
        .file-count {
            color: #667eea;
            font-weight: bold;
        }
        .back-link {
            margin-top: 30px;
            text-align: center;
        }
        @media (max-width: 600px) {
            .container { padding: 20px; }
            .summary { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Categorization Results</h1>
        </div>
        
        <div class="summary">
            <div class="stat">
                <div class="stat-num">{{ processed_count }}</div>
                <div class="stat-label">Processed</div>
            </div>
            <div class="stat">
                <div class="stat-num">{{ failed_count }}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat">
                <div class="stat-num">{{ stats|length }}</div>
                <div class="stat-label">Categories</div>
            </div>
            <div class="stat">
                <div class="stat-num">{{ categorized_files|length }}</div>
                <div class="stat-label">Total Files</div>
            </div>
        </div>
        
        <div class="download-section">
            <h2 style="margin-bottom: 15px; color: #2d3748;">📦 Download Organized Resumes</h2>
            <p style="margin-bottom: 20px; color: #4a5568;">
                Your resumes have been organized into folders by domain and experience level.
            </p>
            <a href="/download" class="btn">📥 Download ZIP File</a>
        </div>
        
        <div class="categories">
            {% for domain, experiences in stats.items() %}
                <div class="category">
                    <h3>🔹 {{ domain.replace('_', ' ') }}</h3>
                    {% for experience, count in experiences.items() %}
                        <div class="experience-group">
                            <div class="experience-title">{{ experience.replace('_', ' ') }}</div>
                            <div class="file-count">{{ count }} files</div>
                        </div>
                    {% endfor %}
                </div>
            {% endfor %}
        </div>
        
        <div class="back-link">
            <a href="/" class="btn btn-secondary">← Process More Resumes</a>
        </div>
    </div>
</body>
</html>
'''

# Clean up old files periodically
def cleanup_old_files():
    """Clean up files older than 1 hour"""
    import time
    current_time = time.time()
    
    for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getctime(file_path)
                if file_age > 3600:  # 1 hour
                    try:
                        os.remove(file_path)
                    except:
                        pass

# Error handlers
@app.errorhandler(413)
def file_too_large(error):
    flash('File too large. Maximum size is 50MB per file.')
    return redirect('/')

@app.errorhandler(404)
def not_found(error):
    return redirect('/')

@app.errorhandler(500)
def internal_error(error):
    flash('An internal error occurred. Please try again.')
    return redirect('/')

# Main execution
if __name__ == '__main__':
    print("🚀 Starting Web Resume Categorizer...")
    print(f"📄 PDF Support: {'Available' if PDF_AVAILABLE else 'Missing (pip install PyPDF2)'}")
    print(f"📝 Word Support: {'Available' if DOCX_AVAILABLE else 'Missing (pip install python-docx)'}")
    print(f"📁 Upload Folder: {UPLOAD_FOLDER}")
    print(f"📦 Processed Folder: {PROCESSED_FOLDER}")
    
    # Clean up old files on startup
    cleanup_old_files()
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Starting server on port {port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
