# 🧾 Automated Invoice Extractor (OCR + Ollama)

**Automated Invoice Extractor** is a Flask-based API that leverages **OCR (EasyOCR)** and **LLMs (Ollama)** to automatically extract, validate, and structure invoice data into clean JSON. It supports invoice image/PDF processing, JSON repair, and rule-based invoice detection for seamless automation.  

---

## 🚀 Features

- **Invoice Data Extraction**  
  Upload an invoice image, extract key fields (company name, GST, invoice number, date, billing/shipping details, line items, taxes, total, etc.).

- **JSON Repair with Ollama**  
  Ensures the extracted output is always valid, properly formatted JSON (no broken keys, no trailing commas, correct numeric types).

- **Invoice Validation**  
  Quickly check if a file is an invoice based on rule-based keyword matching.

- **PDF → Image Conversion**  
  Converts multi-page PDFs into base64-encoded PNG images for OCR processing.

---


---

## 🛠️ Tech Stack

- **Flask** – REST API framework  
- **EasyOCR** – OCR engine for text extraction  
- **Ollama** – LLM-based JSON correction & structured parsing  
- **pdf2image** – PDF to image conversion  
- **PIL (Pillow)** – Image processing  
- **Base64 / JSON / Regex** – Encoding and data handling  

---

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/automated-invoice-extractor.git
   cd automated-invoice-extractor

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows
3. **Install dependencies**
   pip install flask easyocr pdf2image pillow ollama

## Running the Server
python ollama-invoice.py



