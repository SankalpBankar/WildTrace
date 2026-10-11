# 🐅 WildTrace 🌿 — AI-Powered Wildlife Monitoring

**WildTrace** is a computer vision-based wildlife monitoring project designed to detect animals, analyze their movement, and explore individual animal re-identification by comparing wildlife images against a reference gallery.

Initially focusing on **tigers in Tadoba-Andhari Tiger Reserve, Maharashtra, India**, WildTrace aims to assist in identifying potentially matching animal sightings using visual similarity and machine learning.

## ✨ Features

- 🐅 **Animal Detection:** Detect animals in images and video using YOLO models.
- 📸 **Image-Based Re-identification:** Compare wildlife images with a reference gallery to find potential matches.
- 🎥 **Video Processing:** Process videos and extract frames for animal detection and tracking.
- 🧠 **Visual Feature Extraction:** Use image embeddings and similarity matching to compare animal appearances.
- 📍 **Movement Analysis:** Analyze animal movement across video frames.
- 🖥️ **Interactive Web Interface:** Upload and process wildlife media through a React-based frontend.

*Feature availability depends on the models and modules integrated into the current implementation.*

## 🛠️ Tech Stack

Python 🐍 — Core programming language and backend logic

FastAPI ⚡ — Building REST APIs

React ⚛️ — Developing the web interface

OpenCV 🎥 — Image processing and video frame extraction

YOLO 🎯 — Animal detection, if integrated

Image Embeddings & Similarity Matching 🧠 — Comparing animal images for potential re-identification


## 📁 Project Directory Structure 🧠💬

```text

WildTrace/
├── backend/
│   ├── main.py                 # 🚀 FastAPI backend and API endpoints
│   ├── reidentifier.py         # 🐅 Animal re-identification logic
│   ├── uploads/                # 📤 Uploaded wildlife images and videos
│   ├── tiger_gallery/           # 🐯 Reference tiger images
│   └── requirements.txt        # 📦 Python dependencies
│
├── frontend/                   # 💻 React web application
│   ├── public/                 # 🌐 Static assets
│   └── src/                    # ⚛️ UI components and application code
│
├── .gitignore                  # 🛡️ Files excluded from Git
└── README.md                   # 📖 Project documentation

```

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.10 or a version compatible with the project's dependencies
- Node.js and npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/SankalpBankar/WildTrace.git
cd WildTrace
```

### 2. Create a Python Virtual Environment

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Backend Dependencies

From the project root:

```bash
pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables

If the application requires environment variables, create a `.env` file using `.env.example` as a reference.

Never commit API keys, credentials, or other secrets to a public repository.

### 5. Start the Backend

From the project root, run:

```bash
python -m uvicorn backend.main:app --reload
```

Backend URL: http://127.0.0.1:8000

Interactive API documentation: http://127.0.0.1:8000/docs

### 6. Start the Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed in the terminal to access the WildTrace web application.

## 🔍 How It Works

1. **Upload Media:** Submit a wildlife image or video through the web interface.
2. **Process Media:** Prepare images or extract frames from videos.
3. **Detect Animals:** Apply the configured detection model to locate animals.
4. **Extract Features:** Generate visual feature representations for detected animals.
5. **Compare Sightings:** Compare extracted features against images in the reference gallery.
6. **Review Results:** Display potential matches and similarity scores for further inspection.

## ⚠️ Important Notes

- The initial prototype focuses on tiger monitoring and re-identification.
- Similarity scores indicate visual resemblance, not definitive animal identity.
- Results depend on image quality, camera angle, lighting, occlusion, and reference-gallery coverage.
- Model weights and datasets may require separate downloads if they are too large or cannot be redistributed.
- Do not commit secrets, virtual environments, temporary uploads, or generated prediction outputs.
- Ensure that wildlife images and location metadata are shared responsibly and in accordance with applicable permissions and licenses.

## 🚀 Future Improvements

- 🐆 Extend support to additional wildlife species.
- 🎥 Improve identification across multiple video frames.
- 🧠 Evaluate advanced animal re-identification models.
- 📍 Organize sightings by timestamps and location metadata.
- 📊 Develop a wildlife sighting and analytics dashboard.
- 🌿 Support wildlife research and conservation workflows.

---

<div align="center">

### 🌿 WildTrace — Exploring AI for Wildlife Monitoring and Conservation 🐅

*Using computer vision to explore wildlife sightings and support conservation research.*

</div>
