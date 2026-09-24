import os
from flask import Flask, render_template_string, request, send_file
import urllib.request
import json

app = Flask(__name__)
# Geçici dosyaların kaydedileceği güvenli klasör ayarı
UPLOAD_FOLDER = '/tmp' if os.name != 'nt' else os.path.join(os.path.expanduser("~"), "Desktop", "gecici_donusumler")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ConvertAPI gizli kodun başarıyla entegre edildi
CONVERTAPI_SECRET = "jY7jvKeNryyweTDErVKEK3sSWebQ57WD"

# Web sitemizin şık ve sade tasarımı (HTML & CSS)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Online PPTX -> PDF Dönüştürücü</title>
    <style>
        body { font-family: 'Arial', sans-serif; background: #f4f7f6; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; max-width: 400px; width: 90%; }
        h2 { color: #333; margin-bottom: 20px; }
        input[type="file"] { display: none; }
        .file-label { display: block; background: #0078D4; color: white; padding: 12px; border-radius: 6px; cursor: pointer; font-weight: bold; margin-bottom: 15px; transition: 0.3s; }
        .file-label:hover { background: #005a9e; }
        .btn-submit { background: #107C41; color: white; border: none; padding: 12px 25px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 16px; width: 100%; display: none; }
        .btn-submit:hover { background: #0b592e; }
        .status { margin-top: 15px; color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>PPTX to PDF Converter</h2>
        <form action="/convert" method="post" enctype="multipart/form-data" onsubmit="showLoading()">
            <label for="file-upload" class="file-label" id="label-text">📂 PowerPoint Dosyası Seç</label>
            <input id="file-upload" type="file" name="file" accept=".pptx, .ppt" onchange="fileSelected()">
            <button type="submit" id="submit-btn" class="btn-submit">🔒 PDF'e Dönüştür ve İndir</button>
        </form>
        <div id="status" class="status"></div>
    </div>
    <script>
        function fileSelected() {
            const input = document.getElementById('file-upload');
            const label = document.getElementById('label-text');
            const btn = document.getElementById('submit-btn');
            if(input.files.length > 0) {
                label.innerText = "✓ Dosya Seçildi";
                label.style.background = "#2b88d8";
                btn.style.display = "block";
            }
        }
        function showLoading() {
            document.getElementById('status').innerText = "Dönüştürülüyor... Lütfen bekleyin...";
            document.getElementById('submit-btn').style.display = "none";
        }
    </script>
</body>
</html>
"""

def cloud_pptx_to_pdf(input_path, output_path):
    # ConvertAPI bulut sunucularını kullanarak kusursuz dönüşüm yapar
    url = f"https://convertapi.com{CONVERTAPI_SECRET}"
    
    with open(input_path, 'rb') as f:
        file_data = f.read()
        
    boundary = b'----WebKitFormBoundary7MA4YWxkTrZu0gW'
    data = (
        b'--' + boundary + b'\r\n' +
        b'Content-Disposition: form-data; name="File"; filename="input.pptx"\r\n' +
        b'Content-Type: application/vnd.openxmlformats-officedocument.presentationml.presentation\r\n\r\n' +
        file_data + b'\r\n' +
        b'--' + boundary + b'--\r\n'
    )
    
    req = urllib.request.Request(url, data=data)
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary.decode()}')
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        file_url = result['Files'][0]['Url']  # İlk listeden URL güvenli şekilde alınır
        urllib.request.urlretrieve(file_url, output_path)

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files: return "Dosya yok", 400
    file = request.files['file']
    if file.filename == '': return "Dosya secilmedi", 400
    
    if file:
        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(input_path)
        base_name = os.path.splitext(file.filename)[0]
        output_path = os.path.join(UPLOAD_FOLDER, base_name + ".pdf")
        
        try:
            cloud_pptx_to_pdf(input_path, output_path)
            return send_file(output_path, as_attachment=True)
        except Exception as e:
            return f"Dönüştürme Hatası: {str(e)}", 500
        finally:
            if os.path.exists(input_path): os.remove(input_path)
            if os.path.exists(output_path): os.remove(output_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
