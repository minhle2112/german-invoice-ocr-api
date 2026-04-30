# 🇩🇪 German Invoice OCR API

Simple API to extract invoice data (net, gross, VAT) using OCR + AI.

---

## 🚀 Setup

Clone repository:

```bash
git clone <your-repo-url>
cd german-invoice-ocr-api
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

## 🧠 Install OCR (Tesseract)

### Windows

Download Tesseract:
👉 https://github.com/UB-Mannheim/tesseract/wiki

Install and note path (example):

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

Add to PATH **or** set in code:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

---

## 🤖 Install AI (Ollama)

### Install Ollama

```bash
# Windows (PowerShell)
irm https://ollama.com/install.ps1 | iex
```

### Pull model

```bash
ollama pull qwen3:8b
```

Alternative (lighter):

```bash
ollama pull phi3
```

---

## ▶️ Run server

```bash
uvicorn main:app --reload
```

Server will run at:

```text
http://127.0.0.1:8000
```

---

## 🧪 Test API

### Swagger UI

```text
http://127.0.0.1:8000/docs
```

### Curl

```bash
curl -X POST "http://127.0.0.1:8000/extract-invoice" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@invoice.png"
```

---

## 📦 Output example

```json
{
  "net_total": 262.99,
  "gross_total": 312.96,
  "vat_amount": 49.97,
  "vat_rate": 19,
  "currency": "EUR"
}
```

---

## ⚙️ Requirements

* Python 3.10+
* Tesseract OCR
* Ollama (local LLM)

---

## 🧠 Notes

* Currency is normalized to `EUR`
* Hybrid approach: **OCR + regex + AI**
* Works best with German invoices

---
