<div align="center">

# ✨ Story-Gen

### Transform Stories into Stunning Videos with AI

*Powered by Google Gemini • Imagen • Veo*

---

</div>

## 🎯 What is Story-Gen?

Story-Gen is an AI-powered video generation platform that transforms text-based story ideas into complete videos. Simply describe your story, and watch as AI creates characters, scenes, and videos automatically.

## 🚀 Quick Start

### Prerequisites

- 🐍 Python 3.10+
- ⚡ [uv](https://docs.astral.sh/uv/) (recommended package manager)
- ☁️ Google Cloud project with API access

### Installation

**1️⃣ Install uv**

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**2️⃣ Setup Project**

```bash
git clone <repository-url>
cd story-gen
```

**3️⃣ Configure Environment**

Create a `.env` file with your API credentials:

```bash
# 🔑 Required
GEMINI_API_KEY=<your-gemini-api-key>
PROJECT_ID=<your-gcp-project-id>
VEO_PROJECT_ID=<your-veo-project-id>
VEO_STORAGE_BUCKET=<your-gcs-bucket-name>

# ⚙️ Optional
DEFAULT_MODEL_ID=gemini-2.5-pro
PORT=8000
LOCAL_STORAGE=tmp
```

**4️⃣ Launch Application**

```bash
uv sync              # Install dependencies
uv run python main.py # Start server
```

🌐 Open your browser at `http://localhost:8000`

---

## 🎬 Workflow

| Step | Tab | Description |
|------|-----|-------------|
| 1️⃣ | **Idea** | Generate or input your story concept |
| 2️⃣ | **Story** | Configure characters, settings, and plot |
| 3️⃣ | **Visual Storyboard** | Generate videos from scenes |
| 4️⃣ | **Short Ingredients** | Review individual scene videos |
| 5️⃣ | **Big Thing** | View the final merged masterpiece |

---

## ⚡ Key Features

🤖 **Smart Story Generation** - AI creates characters, plots, and scenes from simple ideas
🎨 **Character Creation** - Automated character portraits with Imagen 4.0
🎥 **Video Generation** - Powered by Veo 2.0/3.0/3.1 models
🗣️ **Audio Narration** - Text-to-speech for scene dialogues
🎞️ **Auto Scene Conversion** - Seamless story-to-video pipeline
✂️ **Video Post-Processing** - Merge, loop, and enhance your videos

---

<div align="center">

**Made with ❤️ using Google AI**

</div>
