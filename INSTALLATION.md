# Installation Guide

## System Requirements

### Minimum Requirements
- CPU: 4 cores
- RAM: 8 GB
- Storage: 20 GB
- OS: Ubuntu 22.04, macOS 13+, Windows 11

### Recommended Requirements
- CPU: 8+ cores
- RAM: 16 GB
- Storage: 50 GB SSD
- GPU: Optional for faster OCR

## Prerequisites

### Docker Installation

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

**macOS:**
```bash
brew install docker docker-compose
```

**Windows:**
Download and install Docker Desktop from https://www.docker.com/products/docker-desktop

### Python 3.12 Installation

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3.12 python3.12-venv python3.12-pip
```

**macOS:**
```bash
brew install python@3.12
```

**Windows:**
Download from https://www.python.org/downloads/release/python-3120/

### Node.js 18+ Installation

**Ubuntu/Debian:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**macOS:**
```bash
brew install node@18
```

## Installation Methods

### Method 1: Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd build-agent
```

2. Configure environment:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your settings
```

3. Start all services:
```bash
docker-compose up -d
```

4. Verify installation:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/
```

### Method 2: Local Development

**Backend Setup:**
```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Install Playwright browsers:
```bash
playwright install chromium
```

Install Tesseract OCR language packs:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-ara tesseract-ocr-hin tesseract-ocr-urd

# macOS
brew install tesseract tesseract-lang

# Windows
# Download from https://github.com/UB-Mannheim/tesseract/wiki
```

**Database Setup:**
```bash
# Start PostgreSQL
docker run -d --name buildagent-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=buildagent \
  -p 5432:5432 \
  postgres:16-alpine

# Start Redis
docker run -d --name buildagent-redis \
  -p 6379:6379 \
  redis:7-alpine

# Start ChromaDB
docker run -d --name buildagent-chromadb \
  -p 8001:8000 \
  chromadb/chroma:0.4.22
```

**Run Backend:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Setup:**
```bash
cd frontend
npm install
npm run dev
```

### Method 3: Production Deployment

**Server Preparation:**
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
sudo apt-get install docker.io docker-compose-plugin

# Configure firewall
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000
sudo ufw allow 3000
sudo ufw enable
```

**SSL Certificate (Let's Encrypt):**
```bash
sudo apt-get install certbot
sudo certbot certonly --standalone -d your-domain.com
```

**Deploy:**
```bash
# Clone repository
git clone <repository-url>
cd build-agent

# Configure production environment
cp backend/.env.example backend/.env
# Edit with production settings

# Start with production config
docker-compose -f docker-compose.yml up -d
```

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Application
APP_NAME=BuildAgent
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/buildagent

# Redis
REDIS_URL=redis://localhost:6379/0

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8001

# LLM Providers (at least one required)
OPENAI_API_KEY=sk-your-key-here
GEMINI_API_KEY=AIza-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Security
SECRET_KEY=your-super-secret-key-min-32-chars
ENCRYPTION_KEY=your-encryption-key-32-bytes

# Agent Settings
SAFE_MODE=true
REQUIRE_APPROVAL=false
MAX_RETRIES=3
```

### LLM Provider Setup

**OpenAI:**
1. Sign up at https://platform.openai.com
2. Create an API key
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

**Google Gemini:**
1. Get API key from https://makersuite.google.com/app/apikey
2. Add to `.env`: `GEMINI_API_KEY=AIza...`

**Anthropic Claude:**
1. Get API key from https://console.anthropic.com
2. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

## Verification

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Database
docker exec buildagent-postgres pg_isready -U postgres

# Redis
docker exec buildagent-redis redis-cli ping

# ChromaDB
curl http://localhost:8001/api/v1/heartbeat
```

### Test Task Execution
```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"goal": "Take a screenshot and analyze the screen"}'
```

## Troubleshooting

### Common Issues

**Port Conflicts:**
```bash
# Check port usage
sudo lsof -i :8000
sudo lsof -i :3000
sudo lsof -i :5432

# Change ports in docker-compose.yml or .env
```

**Database Connection:**
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres

# Check logs
docker logs buildagent-postgres
```

**OCR Not Working:**
```bash
# Verify Tesseract installation
tesseract --version

# Check language packs
ls /usr/share/tesseract-ocr/4.00/tessdata/
```

**Permission Denied:**
```bash
# Fix Docker permissions
sudo chown -R $USER:$USER .
sudo chmod -R 755 .
```

## Next Steps

- Access the dashboard at http://localhost:3000
- Configure security policies
- Create your first workflow
- Set up monitoring alerts
