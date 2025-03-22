# Receipt Processor

This project is a **Receipt Processing System** built using **Django** and **Bootstrap**. It allows users to:
- Upload receipts (PDFs)
- Validate receipts
- Extract receipt details using **Tesseract OCR**
- Store and view processed receipts

## 🚀 Features
- File upload and storage
- PDF text extraction using **Tesseract OCR**
- Receipt validation
- Processed receipts table with formatted dates
- Bootstrap UI for a clean interface

---

## 📌 Prerequisites

### 1️⃣ Install System Dependencies
#### Windows
- **Tesseract OCR** → Download from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- **Poppler** → Download from [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases)

After installing Poppler, add its `bin` directory to the **System PATH**:
```sh
setx PATH "%PATH%;C:\path\to\poppler\bin"
```

#### Linux (Ubuntu/Debian)
```sh
sudo apt update
sudo apt install tesseract-ocr poppler-utils
```

#### macOS
```sh
brew install tesseract poppler
```

### 2️⃣ Install Python Dependencies
Ensure you have **Python 3.8+** installed.

```sh
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install -r requirements.txt
```

---

## 🛠️ Project Setup

### 1️⃣ Clone the Repository
```sh
git clone https://github.com/your-username/receipt-processor.git
cd receipt-processor
```

### 2️⃣ Apply Database Migrations
```sh
python manage.py migrate
```

### 3️⃣ Run the Development Server
```sh
python manage.py runserver
```

Your project will be available at **http://127.0.0.1:8000/**

---

## 📂 API Endpoints

### **1️⃣ Upload Receipt**
- **Endpoint:** `POST /api/upload/`
- **Request Body:** `multipart/form-data`
- **Response:** `{ "file_id": 1, "message": "File uploaded successfully" }`

### **2️⃣ Validate Receipt**
- **Endpoint:** `POST /api/validate/`
- **Request Body:** `{ "file_id": 1 }`
- **Response:** `{ "is_valid": true, "message": "File validated successfully" }`

### **3️⃣ Process Receipt**
- **Endpoint:** `POST /api/process/`
- **Request Body:** `{ "file_id": 1 }`
- **Response:** `{ "merchant_name": "Amazon Store", "total_amount": 929.98, "purchased_at": "March 22, 2025" }`

### **4️⃣ Get Stored Receipts**
- **Endpoint:** `GET /api/receipts/`
- **Response:** JSON list of stored receipts

---

## 🎨 Frontend UI
- Uses **Bootstrap** for styling
- Located in `templates/index.html`
- Features:
  - Upload Form
  - Validation Form
  - Processing Form
  - List of stored receipts

---

## 🔐 Superadmin Login
To access the Django admin panel and manage the database:

- **URL:** `http://127.0.0.1:8000/admin/`
- **Username:** `sam`
- **Password:** `Pccoe123`

---

## 🎯 Notes
- Ensure **Tesseract and Poppler** are installed correctly.
- Run the project inside a **virtual environment**.
- I haven't focued much on making good UI, I have gave more time in making REST APIs which is available in shared postman collection.

---

## 👨‍💻 Contributors
- **Samarth Godase** ([GitHub profile](https://github.com/samarth1011))

---
