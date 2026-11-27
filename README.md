# PDF Master - Universal PDF Processing Web Application

A production-ready, cloud-based PDF processing platform inspired by iLovePDF, built with modern technologies and featuring 31 PDF tools across 7 categories.

## Features

### 31 PDF Tools Across 7 Categories

| Category | Tools |
|----------|-------|
| **Organize** | Merge, Split, Rotate, Extract Pages, Organize Pages |
| **Optimize** | Compress, Repair |
| **Security** | Protect (Password), Unlock |
| **Convert** | PDF↔Word, PDF↔JPG, PDF↔Excel, PDF↔PowerPoint |
| **Edit** | Add Text, Add Image, Add Watermark, Add Page Numbers, Add Signature, Add Annotation |
| **Advanced** | OCR, Redact, Compare, Extract Text, Extract Images, Metadata, Page Preview |
| **Platform** | Auto Cleanup, Performance Monitoring, Caching |

### Key Features

- **No Registration Required** - Guest mode with temporary processing
- **Auto File Deletion** - Files deleted within 30 minutes
- **PWA Support** - Installable on all devices (iOS, Android, Desktop)
- **Cross-Platform** - Works on Windows, macOS, iOS, Android
- **Responsive Design** - Mobile-first, works on all screen sizes
- **Dark/Light Theme** - User preference persistence
- **Secure Processing** - HTTPS, rate limiting, file validation
- **No Local Dependencies** - All processing in cloud

## Technology Stack

### Frontend
- **React 18** + Vite 5
- **Tailwind CSS** - Custom design system
- **React Router 6** - SPA routing
- **Lucide React** - Icon library
- **Vite PWA Plugin** - Service worker & manifest
- **Axios** - API communication

### Backend
- **FastAPI** - Modern async Python framework
- **PyMuPDF (fitz)** - Core PDF processing
- **pypdf** - Additional PDF operations
- **pdfplumber** - Text/table extraction
- **pdf2docx** - PDF to Word conversion
- **python-docx** - Word document creation
- **Pillow** - Image processing
- **pytesseract** - OCR (with fallback)
- **LibreOffice** - Document conversions (Docker)
- **Uvicorn** - ASGI server

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Local development
- **Vercel** - Frontend hosting
- **Render** - Backend hosting
- **nginx** - Frontend proxy & static serving

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional, for full stack)

### Local Development

```bash
# Clone repository
git clone <repo-url>
cd pdf-master

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Docker Development

```bash
# Build and start all services
docker-compose up --build

# Access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Project Structure

```
pdf-master/
├── backend/
│   ├── main.py                 # FastAPI application (31 endpoints)
│   ├── Dockerfile              # Backend container
│   ├── requirements.txt        # Python dependencies
│   ├── render.yaml             # Render deployment config
│   ├── middleware/
│   │   └── security.py         # Rate limiting, headers, validation
│   └── services/               # 13 service modules
│       ├── merge.py            # PDF merging
│       ├── split.py            # PDF splitting
│       ├── rotate.py           # Page rotation
│       ├── compress.py         # Compression
│       ├── organize.py         # Page organization
│       ├── protect.py          # Password protection
│       ├── unlock.py           # Password removal
│       ├── repair.py           # PDF repair
│       ├── convert.py          # Format conversions
│       ├── edit.py             # PDF editing
│       ├── advanced.py         # OCR, redact, compare, etc.
│       ├── cleanup.py          # Auto cleanup service
│       ├── performance.py      # Monitoring & caching
│       └── __init__.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js          # Vite + PWA config
│   ├── vercel.json             # Vercel deployment
│   ├── Dockerfile.frontend     # Frontend container
│   ├── nginx.conf              # nginx config with API proxy
│   ├── index.html              # PWA-ready HTML
│   └── src/
│       ├── main.jsx            # Entry point
│       ├── App.jsx             # Main app (28 tools + routing)
│       ├── index.css           # Tailwind + custom styles
│       ├── components/         # 11 reusable components
│       └── serviceWorker.js    # PWA registration
│
├── docker-compose.yml          # Local full-stack
├── .env.production.example     # Production env template
├── TESTING.md                  # Comprehensive test cases
└── README.md
```

## API Endpoints

### Health & Info
- `GET /health` - Health check
- `GET /api/version` - Version info
- `GET /api/tools` - List all tools

### Job Management
- `POST /api/upload` - Generic upload
- `GET /api/jobs/{job_id}` - Job status
- `POST /api/jobs/{job_id}/download` - Download result
- `DELETE /api/jobs/{job_id}` - Delete job

### Organize
- `POST /api/pdf/merge` - Merge multiple PDFs
- `POST /api/pdf/split` - Split PDF by pages
- `POST /api/pdf/rotate` - Rotate pages
- `POST /api/pdf/organize` - Remove/extract/reorder

### Optimize
- `POST /api/pdf/compress` - Compress PDF
- `POST /api/pdf/repair` - Repair corrupted PDF

### Security
- `POST /api/pdf/protect` - Password protect
- `POST /api/pdf/unlock` - Remove password

### Convert
- `POST /api/pdf/to-word` - PDF to Word
- `POST /api/pdf/to-jpg` - PDF to JPG
- `POST /api/jpg-to-pdf` - JPG to PDF
- `POST /api/pdf/to-excel` - PDF to Excel
- `POST /api/excel-to-pdf` - Excel to PDF
- `POST /api/pdf/to-powerpoint` - PDF to PPTX
- `POST /api/powerpoint-to-pdf` - PPTX to PDF

### Edit
- `POST /api/pdf/add-text` - Add text
- `POST /api/pdf/add-image` - Add image
- `POST /api/pdf/add-watermark` - Add watermark
- `POST /api/pdf/add-page-numbers` - Add page numbers
- `POST /api/pdf/add-signature` - Add signature
- `POST /api/pdf/add-annotation` - Add annotation

### Advanced
- `POST /api/pdf/ocr` - OCR processing
- `POST /api/pdf/redact` - Redact content
- `POST /api/pdf/compare` - Compare PDFs
- `POST /api/pdf/extract-text` - Extract text
- `POST /api/pdf/extract-images` - Extract images
- `POST /api/pdf/metadata` - Get metadata
- `POST /api/pdf/preview` - Generate thumbnails

### Monitoring
- `GET /api/performance/stats` - Endpoint performance
- `GET /api/performance/system` - System resources
- `GET /api/cache/stats` - Cache statistics
- `GET /api/storage/usage` - Temp storage usage
- `POST /api/storage/cleanup` - Trigger cleanup

## Deployment

### Frontend (Vercel)

1. Connect GitHub repository to Vercel
2. Configure:
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Framework: Vite
   - Root Directory: `frontend`
3. `frontend/vercel.json` proxies `/api/*` requests to the Render backend. Update its
   rewrite destination if the backend URL changes.

### Backend (Render)

1. Create new Web Service on Render
2. Select Docker runtime
3. Use Dockerfile path `./backend/Dockerfile` and repository-root Docker context (`.`)
4. Configure environment variables from the root `render.yaml`
5. Set Health Check Path: `/health`
6. API documentation is available at `/docs`; the OpenAPI specification is at `/openapi.json`.

### Docker Production

```bash
# Build images
docker-compose -f docker-compose.yml build

# Run production stack
docker-compose -f docker-compose.yml up -d
```

## Security Features

- **Rate Limiting**: 60 req/min, 1000 req/hour per IP
- **File Validation**: Magic bytes, size limits (50MB)
- **Security Headers**: CSP, X-Frame-Options, HSTS
- **Secure Tokens**: Cryptographically random download tokens
- **Auto Cleanup**: 30-minute file retention
- **Path Traversal Protection**: Server-side filename generation
- **CORS Configuration**: Restricted origins in production

## Performance

- **Async Processing**: Background jobs with status polling
- **Concurrency Control**: Per-job locks, max 5 concurrent
- **Caching**: TTL-based async cache
- **Monitoring**: Request timing, error rates, system stats
- **Resource Limits**: Docker CPU/memory constraints

## Testing

See [TESTING.md](TESTING.md) for comprehensive test cases covering:
- 7 categories × multiple scenarios
- Cross-device (desktop, mobile, tablet)
- PWA functionality
- Load & stress testing
- Security validation

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

## Support

For issues and feature requests, please use the GitHub issue tracker.