from flask import Flask, request, jsonify
import easyocr
import tempfile
import os
import re
import json
import ollama
from PIL import Image
from pdf2image import convert_from_path
import base64
import io

app = Flask(__name__)
reader = easyocr.Reader(['en'])

# === Helper functions ===

def extract_text_with_easyocr(image_path):
    result = reader.readtext(image_path, detail=0)
    return "\n".join(result)
def fix_invalid_json_with_ollama(raw_output: str, model="phi3"):
    """
    Uses Ollama to fix broken JSON and return a valid Python dict.
    """
    fix_prompt = f"""
You are a JSON repair expert.

Fix the following broken or improperly formatted JSON to make it valid and strict.
- All keys and string values should be in double quotes.
- No trailing commas.
- Amounts must be numeric (no words or currency symbols).
- Return only the corrected JSON. No explanation, no markdown, no commentary.

Here is the raw output:
\"\"\"{raw_output}\"\"\"
"""

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": fix_prompt}]
        )
        cleaned_output = response['message']['content']

        # Remove any markdown ```json blocks
        cleaned_output = re.sub(r"```(?:json)?", "", cleaned_output).strip("`\n ")
        match = re.search(r"\{(?:[^{}]|(?R))*\}", cleaned_output, re.DOTALL)

        if match:
            return json.loads(match.group(0))
        else:
            return {"error": "Ollama did not return valid JSON.", "raw_output": cleaned_output}
    except Exception as e:
        return {"error": f"Failed to parse/fix JSON: {str(e)}", "raw_output": raw_output}


def run_ollama(prompt, model="llama3.1"):
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response['message']['content']

def parse_json_from_output(output):
    try:
        json_start = output.find('{')
        return json.loads(output[json_start:])
    except Exception:
        return {"raw_output": output.strip()}

def is_invoice_text_rule_based(text):
    keywords = ["invoice", "total", "amount", "bill to", "invoice number", "invoice date"]
    count = sum(1 for word in keywords if word.lower() in text.lower())
    return count >= 2  # Adjust threshold as needed

# === Flask routes ===

@app.route("/extract-invoice", methods=["POST"])
def extract_invoice():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "Empty file name"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_img:
        image_path = temp_img.name
        image_file.save(image_path)

    try:
        ocr_text = extract_text_with_easyocr(image_path)
        prompt = f"""
Extract ONLY the fields from the OCR invoice text. Return a valid **JSON object only** with the following structure. DO NOT return markdown (no ```), explanation, or text before/after JSON.

All numeric fields (e.g., total, tax, RCM) must be numbers (not words). Dates should follow DD-MMM-YYYY. Quantity should be numeric and line items cost and quantity should be accurate numbers. Example:

{{
  "Company Name": "",
  "Vendor GST Number": "",
  "Invoice Number": "",
  "Invoice Date": "",
  "Bill-to Address": "",
  "Ship-to Address": "",
  "RCM Applicable": false,
  "RCM Amount": 0.0,
  "Billing Address": "",
  "Total Amount": 0.0,
  "Tax Total": 0.0,
  "Tax Bifurcation": {{
    "IGST": 0.0,
    "CGST": 0.0,
    "SGST": 0.0
  }},
  "Line Items": [
    {{
      "description": "",
      "quantity": 1,
      "price": 0.0
    }}
  ]
}}

OCR TEXT:
\"\"\"{ocr_text}\"\"\"
"""

        
        output = run_ollama(prompt)
        # extracted_data = parse_json_from_output(output)
        output = json.loads(output)
        return jsonify(output)
    except Exception as e:
        print("fixing json")
        output = fix_invalid_json_with_ollama(output)
        print(output)
        return jsonify(output)

    finally:
            os.remove(image_path)


        
@app.route("/is-invoice", methods=["POST"])
def is_invoice():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "Empty file name"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_img:
        image_path = temp_img.name
        image_file.save(image_path)

    try:
        ocr_text = extract_text_with_easyocr(image_path)
        is_invoice_result = is_invoice_text_rule_based(ocr_text)
        return jsonify({
            "is_invoice": is_invoice_result,
            "reason": "Matched keywords in text" if is_invoice_result else "Not enough invoice-related content"
        })

    finally:
        os.remove(image_path)

# === New endpoint: convert PDF to base64 images ===

@app.route("/convert", methods=["POST"])
def convert_pdf_to_base64_images():
    if 'pdf' not in request.files:
        return jsonify({"error": "No PDF uploaded"}), 400

    pdf_file = request.files['pdf']
    if pdf_file.filename == '':
        return jsonify({"error": "Empty file name"}), 400

    if not pdf_file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Uploaded file is not a PDF"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        pdf_path = temp_pdf.name
        pdf_file.save(pdf_path)

    base64_images = []

    try:
        images = convert_from_path(pdf_path, dpi=300)
        for i, img in enumerate(images):
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            base64_images.append({
                "page": i + 1,
                "image_base64": img_b64
            })

        return jsonify({
            "message": f"Converted {len(base64_images)} pages.",
            "images": base64_images
        })

    except Exception as e:
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500

    finally:
        os.remove(pdf_path)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
