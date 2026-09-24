import os
from flask import Flask, render_template_string, request, send_file
import requests
import time

app = Flask(__name__)
# Bulut sunucusunun (Linux) geçici klasör ayarı
UPLOAD_FOLDER = '/tmp' if os.name != 'nt' else os.path.join(os.path.expanduser("~"), "Desktop", "gecici_donusumler")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ConvertAPI Gizli Anahtarın
CONVERTAPI_SECRET = "jY7jvKeNryyweTDErVKEK3sSWebQ57WD"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Süper Kaliteli PPTX -> PDF Dönüştürücü v2</title>
    <style>
        body { font-family: 'Arial', sans-serif; background: #eef2f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); text-align: center; max-width: 420px; width: 90%; }
        h2 { color: #1e293b; margin-bottom: 5px; font-size: 24px; }
        .version { color: #107C41; font-weight: bold; margin-bottom: 25px; font-size: 14px; }
        input[type="file"] { display: none; }
        .file-label { display: block; background: #0078D4; color: white; padding: 14px; border-radius: 8px; cursor: pointer; font-weight: bold; margin-bottom: 20px; transition: 0.2s; }
        .file-label:hover { background: #005a9e; }
        .btn-submit { background: #107C41; color: white; border: none; padding: 14px 25px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 16px; width: 100%; display: none; box-shadow: 0 4px 12px rgba(16,124,65,0.2); }
        .btn-submit:hover { background: #0b592e; }
        .status { margin-top: 20px; color: #64748b; font-size: 14px; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Bulut PDF Dönüştürücü</h2>
        <div class="version">✨ ConvertAPI Canlı Motoru Aktif ✨</div>
        <form action="/convert" method="post" enctype="multipart/form-data" onsubmit="showLoading()">
            <label for="file-upload" class="file-label" id="label-text">📂 PowerPoint Dosyası Seç (.pptx)</label>
            <input id="file-upload" type="file" name="file" accept=".pptx, .ppt" onchange="fileSelected()">
            <button type="submit" id="submit-btn" class="btn-submit">🚀 Orijinal Tasarımda PDF'e Dönüştür</button>
        </form>
        <div id="status" class="status"></div>
    </div>
    <script>
        function fileSelected() {
            const input = document.getElementById('file-upload');
            const label = document.getElementById('label-text');
            const btn = document.getElementById('submit-btn');
            if(input.files.length > 0) {
                label.innerText = "✓ " + input.files.name;
                label.style.background = "#1e293b";
                btn.style.display = "block";
            }
        }
        function showLoading() {
            document.getElementById('status').innerText = "Bulut motoru slayt tasarımlarınızı orijinal kalitede işliyor... Lütfen bekleyin...";
            document.getElementById('submit-btn').style.display = "none";
        }
    </script>
</body>
</html>
"""

def cloud_pptx_to_pdf(input_path, output_path):
    # Sabit ve kesinlikle bozulmayacak temiz internet adresi
    url = f"https://convertapi.com{CONVERTAPI_SECRET}"
    
    with open(input_path, 'rb') as f:
        files = {'File': f}
        response = requests.post(url, files=files)
        
    if response.status_code == 200:
        result = response.json()
        file_url = result['Files'][0]['Url']  # İlk dosyanın indirme URL'ini güvenli şekilde çeker
        
        # Kaliteli PDF dosyasını buluttan indiriyoruz
        file_response = requests.get(file_url)
        with open(output_path, 'wb') as out_f:
            out_f.write(file_response.content)
    else:
        raise Exception(f"Bulut Servis Hatasi: {response.text}")

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files: return "Dosya yok", 400
    file = request.files['file']
    if file.filename == '': return "Dosya secilmedi", 400
    
    if file:
        # Zaman damgası ekleyerek sunucuda benzersiz isim oluşturuyoruz
        timestamp = str(int(time.time()))
        unique_input_name = timestamp + "_" + file.filename
        input_path = os.path.join(UPLOAD_FOLDER, unique_input_name)
        file.save(input_path)
        
        # [0] eklenerek splitext fonksiyonunun tuple hatası vermesi kesin olarak engellendi
        pure_name = os.path.splitext(file.filename)[0]
        output_filename = timestamp + "_" + pure_name + ".pdf"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
        try:
            cloud_pptx_to_pdf(input_path, output_path)
            # Kullanıcıya kendi yüklediği orijinal dosya adıyla indirtiyoruz
            original_pdf_name = pure_name + ".pdf"
            return send_file(output_path, as_attachment=True, download_name=original_pdf_name)
        except Exception as e:
            return f"Dönüştürme Hatası: {str(e)}", 500
        finally:
            # İşlem bittiğinde sunucudaki geçici dosyaları siliyoruz
            if os.path.exists(input_path): os.remove(input_path)
            if os.path.exists(output_path): os.remove(output_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
