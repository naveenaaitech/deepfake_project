# SPECULUM — AI-Powered Deepfake Video Detection System

An end-to-end, production-grade Deepfake Video Detection web platform built for high-accuracy media forensics. **SPECULUM** accepts uploaded videos, extracts human faces with high-speed neural face detection, analyzes facial micro-textures using a pretrained **Vision Transformer (ViT)**, and classifies the footage into **REAL**, **DEEPFAKE**, or **INCONCLUSIVE** with confidence telemetry and forensic explanations.

---

## 🌟 Key Features

- **Trained AI Vision Transformer (ViT)**: Replaces heuristic approximations with a deep learning classification pipeline based on ViT (`dima806/deepfake_vs_real_image_detection`).
- **High-Speed YuNet Face Detection**: Uses an optimized ONNX face detector with 640px scaled inference for ultra-fast face extraction across standard and 4K UHD videos.
- **Foreground-Aware Forensic Aggregation**: Accurately isolates primary subjects from background bystanders and distinguishes natural camera sensor reflections (such as eyeglasses glare) from synthetic AI generation artifacts.
- **Asynchronous Non-Blocking Processing**: Video inference runs in a daemon background worker thread, ensuring HTTP requests never time out while the frontend dynamically polls for results.
- **Interactive Modern Dashboard**: Dark-mode forensic telemetry interface with drag-and-drop intake, live model health badges, confidence gauges, and historical verification logs.
- **Full Offline Portability**: Pretrained model weights are bundled directly inside the project directory (`models/`), allowing the system to run completely offline without external API keys or cloud dependencies.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | **Django 4.x / 5.x / 6.x** | Core web framework, routing, and media handling |
| **REST API** | **Django REST Framework (DRF)** | Serialization and RESTful endpoint design |
| **Deep Learning** | **PyTorch & Hugging Face Transformers** | Vision Transformer (`ViT`) inference for face authenticity |
| **Computer Vision** | **OpenCV (cv2) & YuNet ONNX** | Video decoding, keyframe extraction, and face detection |
| **Database** | **SQLite3** | Zero-configuration relational database for analysis history |
| **Frontend** | **HTML5, CSS3, Vanilla JavaScript** | Glassmorphic UI, real-time polling, and drag-and-drop intake |

---

## 📁 Project Directory Structure

```text
demo_deepfake/
│
├── manage.py                          # Django management script
├── requirements.txt                   # Project Python dependencies
├── README.md                          # This documentation file
├── db.sqlite3                         # Pre-configured SQLite database
│
├── myproject/                         # Django project settings & URL routing
│   ├── settings.py                    # App configuration, media paths, CORS
│   ├── urls.py                        # Root URL routing
│   └── wsgi.py                        # WSGI entry point
│
├── myapp/                             # Core forensic analysis application
│   ├── models.py                      # VideoAnalysis model schema
│   ├── views.py                       # REST API views & async background worker
│   ├── serializers.py                 # DRF serializers
│   ├── urls.py                        # API routes (/api/upload/, /api/analyze/, etc.)
│   ├── tests.py                       # Automated unit and integration test suite
│   │
│   ├── services/                      # Modular AI & CV forensic engine
│   │   ├── deepfake_detector.py       # ViT singleton loader & aggregation logic
│   │   └── video_processor.py         # OpenCV frame & YuNet face extraction
│   │
│   ├── templates/
│   │   └── index.html                 # Single-page dashboard template
│   │
│   └── static/                        # Frontend UI assets
│       ├── css/style.css              # Cyber-forensic dark-mode styling
│       └── js/script.js               # Async polling & UI state management
│
├── models/                            # Offline Pretrained Model Storage
│   ├── deepfake_detector/vit/         # Vision Transformer weights & configs
│   │   ├── model.safetensors          # Deepfake classifier neural weights
│   │   ├── config.json                # Model architecture configuration
│   │   └── preprocessor_config.json   # Normalization parameters
│   │
│   └── face_detector/                 # OpenCV YuNet ONNX Face Detector
│       └── face_detection_yunet_2023mar.onnx
│
└── media/                             # Storage for uploaded media assets
    └── videos/                        # Uploaded MP4/AVI/MOV video files
```

---

## 🚀 Beginner Quick-Start Guide

Follow these steps after unzipping the project folder to run the application on your computer.

### Prerequisites

- **Python 3.10, 3.11, 3.12, 3.13, or 3.14** installed on your system.
  - Check your version in terminal: `python --version`
- **pip** (Python package manager, bundled with Python).

---

### Step 1: Open the Project Directory

Open your terminal or command prompt and navigate to the extracted project folder:

**Windows (Command Prompt / PowerShell):**
```powershell
cd path\to\extracted_folder
```

**macOS / Linux:**
```bash
cd /path/to/extracted_folder
```

---

### Step 2: (Recommended) Create a Virtual Environment

Creating an isolated virtual environment prevents conflicts with existing Python packages.

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

*(When activated, you will see `(venv)` at the beginning of your command line).*

---

### Step 3: Install Required Dependencies

Install the required packages using `requirements.txt`:

```bash
pip install -r requirements.txt
```

> **Note**: CPU-only PyTorch is installed by default and runs inference in 1–3 seconds per video. If you have an NVIDIA GPU with CUDA, PyTorch will automatically accelerate inference.

---

### Step 4: Apply Database Migrations

Set up the database schema for the analysis records:

```bash
python manage.py migrate
```

---

### Step 5: Start the Development Server

Launch the Django development server:

```bash
python manage.py runserver
```

You should see output similar to:
```text
System check identified no issues (0 silenced).
Django version 6.1.1, using settings 'myproject.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

### Step 6: Open the Dashboard

Open your web browser (Chrome, Edge, Firefox, Safari) and navigate to:

👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 🧪 How to Demo and Test the System

### Test 1: Uploading an Authentic (Real) Camera Video
1. Record a short 3–10 second video of yourself using your phone or laptop camera (e.g. Windows Camera app).
2. Drag and drop the `.mp4` video into the intake box on the dashboard.
3. Click **"Analyze Video"**.
4. The status badge will change from `PENDING` $\rightarrow$ `PROCESSING` $\rightarrow$ `COMPLETED`.
5. Verdict will display **`REAL`** with confidence score (e.g., `83.2% Authentic`) and forensic verification details.

### Test 2: Uploading an AI-Generated or Deepfake Video
1. Upload an AI-generated video (such as a Runway/Sora/Kling generation or FaceForensics/Deepfake video).
2. Click **"Analyze Video"**.
3. Verdict will display **`DEEPFAKE`** with confidence score (e.g., `94.2% – 99.3%`) highlighting synthetic manipulation artifacts.

### Test 3: Uploading a Video with No Human Faces
1. Upload a video of scenery, objects, or animals without human faces.
2. Click **"Analyze Video"**.
3. Verdict will display **`INCONCLUSIVE`** (`0.0% Confidence`) with the explanation: *"No human faces were detected in the video frames. Face-based deepfake analysis is inconclusive."*

---

## 🔬 Running Automated Unit Tests

The project includes an automated test suite verifying file validation, API endpoints, background execution, and model inference.

Run the tests with:

```bash
python manage.py test myapp
```

Expected output:
```text
Ran 8 tests in ~5.8s

OK
```

---

## 📡 REST API Reference

The backend exposes a clean REST API consumable by web and mobile clients:

### 1. Upload Video
- **Endpoint**: `POST /api/upload/`
- **Content-Type**: `multipart/form-data`
- **Body**: `video`: `<binary file>`
- **Response** (`201 Created`):
```json
{
  "id": 42,
  "video": "/media/videos/sample.mp4",
  "status": "pending",
  "result": "",
  "confidence": null,
  "error_message": "",
  "created_at": "2026-10-14T14:30:00Z"
}
```

### 2. Trigger Analysis
- **Endpoint**: `POST /api/analyze/<id>/`
- **Description**: Spawns an asynchronous background worker thread to process the video.
- **Response** (`200 OK`):
```json
{
  "id": 42,
  "status": "processing",
  "message": "Analysis started in background"
}
```

### 3. Retrieve Analysis Result
- **Endpoint**: `GET /api/result/<id>/`
- **Description**: Polled by the frontend until `status` becomes `completed` or `failed`.
- **Response** (`200 OK`):
```json
{
  "id": 42,
  "status": "completed",
  "result": "deepfake",
  "confidence": 0.942,
  "error_message": "Detected persistent synthetic facial manipulation artifacts on the primary subject.",
  "created_at": "2026-10-14T14:30:00Z"
}
```

### 4. Analysis History
- **Endpoint**: `GET /api/history/`
- **Description**: Returns the list of past analyses ordered by most recent first.

---

## 🧠 Forensic Detection Architecture

```text
[ Video File ] 
      │
      ▼
[ Validation & OpenCV Decoding ] (Frame rate, dimensions, corruption check)
      │
      ▼
[ Keyframe Extraction ] (Evenly distributed sample frames)
      │
      ▼
[ OpenCV YuNet ONNX ] (High-speed 640px face detection)
      │
      ▼
[ Square Anti-Aliased Face Cropping ] (Aspect ratio preservation without distortion)
      │
      ▼
[ Vision Transformer (ViT) Inference ] (Batch feature extraction & softmax classification)
      │
      ▼
[ Foreground-Aware Decision Hierarchy ]
   ├─ Filters out small background bystanders (< 20% area)
   ├─ Identifies primary subject biological pore & texture markers (Authentic Anchor)
   └─ Evaluates synthetic diffusion & boundary blending energy
      │
      ▼
[ Verdict: REAL | DEEPFAKE | INCONCLUSIVE ] -> Saved to SQLite & Streamed to Dashboard
```

---

## 🛡️ License & Acknowledgements

- **Model Backbone**: Vision Transformer fine-tuned for deepfake vs. real detection (`dima806/deepfake_vs_real_image_detection`).
- **Face Detector**: OpenCV YuNet Face Detection model (OpenCV Model Zoo).
- Built for academic research, hackathons, and digital media authentication.
