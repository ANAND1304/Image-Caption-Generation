# 🖼️ AI Image Caption Generator

A production-grade Image Caption Generator using CNN + LSTM with Attention Mechanism, FastAPI backend, and React frontend.

![Tech Stack](https://img.shields.io/badge/ML-PyTorch-orange) ![Backend](https://img.shields.io/badge/Backend-FastAPI-green) ![Frontend](https://img.shields.io/badge/Frontend-React-blue) ![Docker](https://img.shields.io/badge/Deploy-Docker-blue)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                  React Frontend                  │
│         (Drag & Drop → Preview → Caption)        │
└─────────────────┬───────────────────────────────┘
                  │ Axios HTTP
┌─────────────────▼───────────────────────────────┐
│              FastAPI Backend                     │
│    (Auth · Rate Limit · Redis Cache · Logging)   │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│           ML Model (PyTorch)                     │
│  ResNet50 → Attention → LSTM → Beam Search       │
└─────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
image-caption-generator/
├── frontend/                    # React.js application
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Page components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── utils/               # Utility functions
│   │   └── styles/              # Global styles
│   ├── package.json
│   └── vite.config.js
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── api/                 # Route handlers
│   │   ├── core/                # Config, security, middleware
│   │   ├── models/              # ML model classes
│   │   ├── services/            # Business logic
│   │   └── utils/               # Helpers
│   ├── tests/                   # Unit tests
│   ├── main.py
│   └── requirements.txt
├── model/                       # ML training scripts
│   ├── scripts/
│   │   ├── train.py             # Full training pipeline
│   │   ├── evaluate.py          # BLEU score evaluation
│   │   └── preprocess.py        # Dataset preprocessing
│   └── weights/                 # Saved model weights
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Redis (or use Docker)
- CUDA GPU (optional, for training)

---

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repo
git clone https://github.com/yourname/image-caption-generator.git
cd image-caption-generator

# Start all services
docker-compose -f docker/docker-compose.yml up --build

# Access:
# Frontend → http://localhost:5173
# Backend API → http://localhost:8000
# API Docs → http://localhost:8000/docs
```

---

### Option 2: Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your settings

# Start Redis (if not using Docker)
redis-server

# Run FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local: VITE_API_URL=http://localhost:8000

# Start development server
npm run dev
```

---

## 🧠 Model Training

### 1. Download Dataset

```bash
# Flickr8k Dataset
cd model/scripts
python download_data.py --dataset flickr8k

# Or manually download from Kaggle:
# https://www.kaggle.com/datasets/adityajn105/flickr8k
```

### 2. Preprocess Data

```bash
python preprocess.py \
  --images_dir ../data/flickr8k/images \
  --captions_file ../data/flickr8k/captions.txt \
  --output_dir ../data/processed
```

### 3. Train Model

```bash
python train.py \
  --data_dir ../data/processed \
  --epochs 20 \
  --batch_size 32 \
  --embed_dim 256 \
  --attention_dim 256 \
  --decoder_dim 512 \
  --save_dir ../weights
```

### 4. Evaluate (BLEU Score)

```bash
python evaluate.py \
  --model_path ../weights/best_model.pt \
  --data_dir ../data/processed
```

Expected BLEU-4 score: **~28-32** on Flickr8k test set.

---

## 🔌 API Reference

### POST `/generate-caption`

Generate a caption for an uploaded image.

**Request:**
```
Content-Type: multipart/form-data
Authorization: Bearer <token>  (if auth enabled)

image: <file>
beam_size: 3  (optional, 1-5)
```

**Response:**
```json
{
  "caption": "a dog running on the beach",
  "confidence": 0.847,
  "processing_time_ms": 245,
  "cached": false
}
```

### GET `/health`

Health check endpoint.

```json
{
  "status": "healthy",
  "model_loaded": true,
  "redis_connected": true
}
```

---

## 🌐 Deployment

### Backend → AWS EC2 / Render

```bash
# Build Docker image
docker build -f docker/Dockerfile.backend -t caption-backend .

# Push to ECR / Docker Hub
docker tag caption-backend your-registry/caption-backend:latest
docker push your-registry/caption-backend:latest

# Deploy on EC2
ssh ec2-user@your-ec2-ip
docker pull your-registry/caption-backend:latest
docker run -d -p 8000:8000 --env-file .env caption-backend
```

### Frontend → Vercel

```bash
cd frontend
npm run build

# Deploy to Vercel
npx vercel --prod
```

---

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Test specific endpoint
pytest tests/test_api.py::test_generate_caption -v
```

---

## ⚡ Performance

| Metric | Value |
|--------|-------|
| Inference Time | ~200-400ms |
| BLEU-4 Score | ~28-32 |
| Cache Hit Rate | ~40% (typical) |
| Max Image Size | 10MB |
| Supported Formats | JPEG, PNG, WEBP, GIF |

---

## 🔧 Environment Variables

### Backend `.env`
```env
# App
APP_NAME=ImageCaptionGenerator
DEBUG=false
SECRET_KEY=your-secret-key-here

# Redis
REDIS_URL=redis://localhost:6379

# Model
MODEL_PATH=../model/weights/best_model.pt
VOCAB_PATH=../model/weights/vocab.pkl
BEAM_SIZE=3

# Rate Limiting
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_PERIOD=60

# CORS
ALLOWED_ORIGINS=http://localhost:5173,https://yourdomain.com
```

### Frontend `.env.local`
```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=CaptionAI
```

---

## 📄 License

MIT License — free for personal and commercial use.

---

## 🙏 Credits

- Flickr8k Dataset — University of Illinois
- ResNet50 — Microsoft Research
- Attention Mechanism — "Show, Attend and Tell" (Xu et al., 2015)
