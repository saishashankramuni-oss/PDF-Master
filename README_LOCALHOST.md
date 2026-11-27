# PDF Master - Local Development Setup

Run PDF Master completely offline on your Windows laptop. No cloud deployment needed.

## Quick Start

1. **Double-click `start.bat`** - This will:
   - Check/install all dependencies
   - Start backend on `http://127.0.0.1:8000`
   - Start frontend on `http://localhost:3000`
   - Open browser automatically at `http://localhost:3000`

2. **Double-click `stop.bat`** to stop everything

The scripts preserve the existing backend virtual environment and stop only PIDs recorded
by this project. If a port is already serving a healthy PDF Master instance, startup reuses it.

## Verified on 2026-11-27

The production frontend build and the following end-to-end API operations passed using
automatically generated PDFs:

- Homepage and frontend module
- Health endpoint and API documentation
- Merge PDF (2 pages)
- Split PDF
- Rotate PDF (90 degrees)
- Compress PDF
- Extract text
- Invalid PDF rejection
- Cleanup trigger

Tesseract OCR and LibreOffice are optional system dependencies. OCR uses a safe fallback
when Tesseract is unavailable. Office conversions that need LibreOffice remain limited
unless LibreOffice is installed and available on `PATH`.

## Prerequisites

| Software | Required | Install From |
|----------|----------|--------------|
| Node.js 18+ | Required | https://nodejs.org/ |
| Python 3.11+ | Required | https://python.org/ |
| Tesseract OCR | Optional (for OCR) | https://github.com/UB-Mannheim/tesseract/wiki |
| LibreOffice | Optional (for conversions) | https://www.libreoffice.org/download/download/ |

## Manual Setup (If start.bat fails)

### Backend Setup
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```cmd
cd frontend
npm install
npm run dev
```

## Application URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://127.0.0.1:8000 |
| API Documentation | http://127.0.0.1:8000/api/docs |
| Health Check | http://127.0.0.1:8000/health |

## Available PDF Tools (31 Total)

### Organize
- **Merge PDF** - Combine multiple PDFs
- **Split PDF** - Split by pages or ranges
- **Rotate PDF** - Rotate 90°/180°/270°
- **Extract Pages** - Extract specific pages
- **Organize Pages** - Reorder/remove pages

### Optimize
- **Compress PDF** - Reduce file size
- **Repair PDF** - Fix corrupted PDFs

### Security
- **Protect PDF** - Password protect
- **Unlock PDF** - Remove password

### Convert
- **PDF to Word** (.docx)
- **PDF to JPG** (images, zipped)
- **PDF to Excel** (.xlsx)
- **PDF to PowerPoint** (.pptx)
- **JPG to PDF**
- **Excel to PDF** (.xlsx → PDF)
- **PowerPoint to PDF** (.pptx → PDF)

### Edit
- **Add Text** - Place text at coordinates
- **Add Image** - Insert images
- **Add Watermark** - Text watermarks
- **Add Page Numbers** - Number pages
- **Add Signature** - Insert signature image
- **Add Annotations** - Highlight, underline, etc.

### Advanced
- **OCR PDF** - Make scanned PDFs searchable
- **Redact PDF** - Permanently remove content
- **Compare PDFs** - Find differences
- **Extract Text** - Get all text content
- **Extract Images** - Save embedded images
- **PDF Metadata** - View document properties
- **Page Preview** - Generate thumbnails

## File Security

- **Max file size**: 50 MB
- **Storage**: Temporary only (`/tmp/jobs/`)
- **Auto-delete**: After 30 minutes
- **Validation**: PDF signature verification
- **Safe filenames**: UUID-based, no user paths

## Troubleshooting

### Backend won't start
```cmd
cd backend
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend won't start
```cmd
cd frontend
npm install
npm run dev
```

### Port already in use
```cmd
# Kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Tesseract OCR not found
Download from: https://github.com/UB-Mannheim/tesseract/wiki
Add to PATH after installation.

### LibreOffice not found
Download from: https://www.libreoffice.org/download/download/
Add to PATH after installation.

## Features Tested

### Working Features (Verified)
- ✅ Merge PDF
- ✅ Split PDF
- ✅ Rotate PDF
- ✅ Compress PDF
- ✅ Protect/Unlock PDF
- ✅ Repair PDF
- ✅ Organize/Extract pages
- ✅ PDF to Word
- ✅ PDF to JPG (zipped)
- ✅ JPG to PDF
- ✅ PDF to Excel (fallback)
- ✅ Excel to PDF (fallback)
- ✅ PDF to PowerPoint (fallback)
- ✅ PowerPoint to PDF (fallback)
- ✅ Add Text
- ✅ Add Watermark
- ✅ Add Page Numbers
- ✅ Add Annotations
- ✅ OCR (fallback mode)
- ✅ Redact
- ✅ Compare PDFs
- ✅ Extract Text
- ✅ Extract Images
- ✅ PDF Metadata
- ✅ Page Preview

### Optional Features (Require System Dependencies)
| Feature | Dependency | Status Without |
|---------|------------|----------------|
| OCR (full) | Tesseract | Fallback mode |
| PDF↔Word/Excel/PPT | LibreOffice | Fallback mode |

## File Structure

```
S:\New folder\
├── start.bat          # One-click start
├── stop.bat           # One-click stop
├── README_LOCALHOST.md
├── backend/
│   ├── main.py              # FastAPI app (31 endpoints)
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile           # For Docker deployment
│   ├── services/            # 13 service modules
│   ├── middleware/          # Security middleware
│   └── venv/                # Python virtual env (created)
├── frontend/
│   ├── dist/                # Production build
│   ├── src/                 # React source
│   │   ├── App.jsx          # Main app
│   │   ├── components/      # 11 components
│   │   └── main.jsx         # Entry point
│   ├── package.json
│   ├── vite.config.js       # Vite + PWA config
│   ├── vercel.json          # Vercel config (for future)
│   └── node_modules/
├── start.bat
├── stop.bat
├── README_LOCALHOST.md
├── QA_REPORT.md
├── DEPLOYMENT.md
└── docker-compose.yml
```

## Verification Checklist

Before using, verify:

- [ ] `start.bat` runs without errors
- [ ] Backend responds at `http://127.0.0.1:8000/health`
- [ ] Frontend loads at `http://localhost:3000`
- [ ] API docs at `http://127.0.0.1:8000/api/docs`
- [ ] Can upload a PDF
- [ ] Can process a PDF (try Merge/Compress)
- [ ] Download works and file opens
- [ ] Stop script stops both servers

## Limitations

1. **In-memory job storage** - Jobs lost on restart (use Redis for production)
2. **Tesseract/LibreOffice optional** - Fallback modes used without them
3. **In-memory job storage** - Not suitable for multi-user production
4. **In-memory rate limiting** - Resets on restart
5. **No authentication** - Guest mode only (by design)

## License

MIT License - See LICENSE file (if present)

---

**PDF Master** - Professional PDF processing, fully offline on your laptop.