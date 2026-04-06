from flask import Flask, request, jsonify
from flask_cors import CORS
import easyocr
import base64
import io
from PIL import Image
import traceback

app = Flask(__name__)
CORS(app)

reader = easyocr.Reader([
    'en', 'fr', 'de', 'es', 'pt',
    'it', 'nl', 'pl', 'ru', 'zh'
], gpu=False)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "i-ScanDoc OCR Server is running ✅"})

@app.route('/ocr', methods=['POST'])
def extract_text():
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"error": "No image provided"}), 400

        image_data = base64.b64decode(data['image'])
        image = Image.open(io.BytesIO(image_data)).convert('RGB')
        results = reader.readtext(image, detail=1, paragraph=False)
        results.sort(key=lambda x: (round(x[0][0][1] / 20), x[0][0][0]))

        lines = []
        current_line = []
        current_y = None

        for bbox, text, confidence in results:
            y_pos = round(bbox[0][1] / 20)
            if current_y is None:
                current_y = y_pos
            if abs(y_pos - current_y) <= 1:
                current_line.append(text)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [text]
                current_y = y_pos

        if current_line:
            lines.append(' '.join(current_line))

        full_text = '\n'.join(lines)

        return jsonify({
            "success": True,
            "text": full_text,
            "lines": lines,
            "word_count": len(full_text.split())
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
