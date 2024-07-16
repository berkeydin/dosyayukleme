from flask import Flask, request, render_template, redirect, url_for
import os
from werkzeug.utils import secure_filename
import pandas as pd
import docx
from PyPDF2 import PdfReader
import datetime
import chardet

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'xls', 'xlsx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def read_docx(file_path):
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def read_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        full_text = []
        for page in reader.pages:
            full_text.append(page.extract_text())
        return '\n'.join(full_text)


def read_xls(file_path):
    df = pd.read_excel(file_path)
    return df.to_string()


def read_txt(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
    
    with open(file_path, 'r', encoding=encoding) as file:
        return file.read()


# Dosya metadata bilgilerini okur
def get_file_metadata(file_path):
    stat_info = os.stat(file_path)
    metadata = {
        'yazar': 'Unknown',  
        'oluşturma_tarihi': datetime.datetime.fromtimestamp(stat_info.st_ctime),
        'sahibi': 'Unknown',  
    }
    return metadata


def search_keyword(content, keyword):
    return keyword.lower() in content.lower()


def search_excel(file_path, keyword):
    df = pd.read_excel(file_path)
    search_results = df[df.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]
    return search_results.to_dict(orient='records')

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/uploader', methods=['GET', 'POST'])
def uploader_file():
    if request.method == 'POST':
        files = request.files.getlist("file")
        results = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

               
                if filename.endswith('.docx'):
                    content = read_docx(file_path)
                elif filename.endswith('.pdf'):
                    content = read_pdf(file_path)
                elif filename.endswith('.xls') or filename.endswith('.xlsx'):
                    content = read_xls(file_path)
                elif filename.endswith('.txt'):
                    content = read_txt(file_path)
                else:
                    content = ''

                
                metadata = get_file_metadata(file_path)

                results.append({
                    'filename': filename,
                    'metadata': metadata,
                })

        return render_template('results.html', results=results)

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form.get('keyword')
    search_results = []

    for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
        for file in files:
            file_path = os.path.join(root, file)
            if allowed_file(file):
                if file.endswith('.xls') or file.endswith('.xlsx'):
                    search_results.extend(search_excel(file_path, keyword))

    return render_template('search_results.html', search_results=search_results)

if __name__ == '__main__':
    app.run(debug=True)