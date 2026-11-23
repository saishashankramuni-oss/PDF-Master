# PDF Master - Testing Guide

## Test Environment Setup

### Local Development Testing
```bash
# Start backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Start frontend (in another terminal)
cd frontend
npm install
npm run dev
```

## Test Cases by Category

### 1. Core PDF Operations (Organize)

#### Merge PDF
- [ ] Merge 2 single-page PDFs
- [ ] Merge 5 multi-page PDFs
- [ ] Merge PDFs with different page sizes
- [ ] Merge large PDFs (25MB each)
- [ ] Error: Non-PDF file rejected
- [ ] Error: Empty file rejected
- [ ] Error: Corrupted PDF rejected

#### Split PDF
- [ ] Split 10-page PDF into individual pages
- [ ] Split by page range (pages 2-5)
- [ ] Split by specific pages (1,3,5)
- [ ] Error: Invalid page numbers
- [ ] Error: Page number exceeds total pages

#### Rotate PDF
- [ ] Rotate 90° clockwise
- [ ] Rotate 180°
- [ ] Rotate 270° clockwise
- [ ] Rotate specific pages only
- [ ] Multiple rotations (90° then 180°)

#### Organize Pages
- [ ] Remove pages 2,4 from 5-page PDF
- [ ] Extract pages 1,3 to new PDF
- [ ] Reorder pages (3,1,2)
- [ ] Move page 3 to position 1
- [ ] Error: Remove all pages

### 2. Optimize Operations

#### Compress PDF
- [ ] Low quality compression
- [ ] Medium quality compression
- [ ] High quality compression
- [ ] Target size compression (under 1MB)
- [ ] Verify output file is smaller

#### Repair PDF
- [ ] Repair slightly corrupted PDF
- [ ] Repair PDF with missing xref
- [ ] Aggressive repair mode
- [ ] Error: Severely corrupted PDF

### 3. Security Operations

#### Protect PDF
- [ ] Password protect with user password
- [ ] Password protect with owner password
- [ ] Set permissions (no print, no copy)
- [ ] Verify protection works

#### Unlock PDF
- [ ] Unlock with correct password
- [ ] Error: Incorrect password
- [ ] Unlock non-protected PDF (should pass through)

### 4. Conversion Operations

#### PDF to Word
- [ ] Simple text PDF to Word
- [ ] Multi-page PDF to Word
- [ ] PDF with tables to Word
- [ ] Scanned PDF to Word (fallback)

#### Word to PDF
- [ ] Simple .docx to PDF
- [ ] .docx with images to PDF
- [ ] .docx with tables to PDF

#### PDF to JPG
- [ ] Single page PDF to JPG
- [ ] Multi-page PDF to ZIP of JPGs
- [ ] Custom DPI (150, 300)
- [ ] PNG output option

#### JPG to PDF
- [ ] Single JPG to PDF
- [ ] Multiple JPGs to multi-page PDF
- [ ] Mixed JPG/PNG to PDF

#### PDF to Excel
- [ ] Table PDF to Excel
- [ ] Multi-table PDF

#### Excel to PDF
- [ ] Simple spreadsheet to PDF
- [ ] Multi-sheet workbook

#### PDF to PowerPoint
- [ ] Simple PDF to PPTX

#### PowerPoint to PDF
- [ ] Simple PPTX to PDF

### 5. Edit Operations

#### Add Text
- [ ] Add text at specific coordinates
- [ ] Custom font size and color
- [ ] Rotated text
- [ ] Unicode text support

#### Add Image
- [ ] Add JPG image
- [ ] Add PNG with transparency
- [ ] Resize image to specific dimensions
- [ ] Maintain aspect ratio

#### Add Watermark
- [ ] Text watermark (default)
- [ ] Custom watermark text
- [ ] Custom position and rotation
- [ ] Opacity control
- [ ] Specific pages only

#### Add Page Numbers
- [ ] Default format (1/5)
- [ ] Custom format (Page {page} of {total})
- [ ] Bottom center, bottom left, bottom right
- [ ] Top positions
- [ ] Custom font and color
- [ ] Specific pages only

#### Add Signature
- [ ] Add signature image
- [ ] Position and size control

#### Add Annotation
- [ ] Highlight text
- [ ] Underline
- [ ] Strikeout
- [ ] Free text annotation
- [ ] Square/Circle
- [ ] Custom color and opacity

### 6. Advanced Operations

#### OCR PDF
- [ ] OCR on scanned PDF (fallback mode)
- [ ] Language selection
- [ ] Output remains searchable

#### Redact PDF
- [ ] Redact specific area
- [ ] Multiple redactions
- [ ] Custom redaction color
- [ ] Verify content unrecoverable

#### Compare PDF
- [ ] Compare identical PDFs
- [ ] Compare with text changes
- [ ] Compare with page count difference
- [ ] Output JSON format

#### Extract Text
- [ ] Extract from simple PDF
- [ ] Extract from multi-page PDF
- [ ] Word/character count accuracy

#### Extract Images
- [ ] Extract embedded images
- [ ] Multiple images per page
- [ ] Base64 encoding in output

#### PDF Metadata
- [ ] View basic metadata
- [ ] Page dimensions
- [ ] Encryption status
- [ ] PDF version

#### Page Preview
- [ ] Generate thumbnails
- [ ] Custom DPI
- [ ] Max pages limit
- [ ] Base64 output

### 7. Platform Features

#### Job Management
- [ ] Upload file → get job_id
- [ ] Poll job status
- [ ] Download with token
- [ ] Token expiration (30 min)
- [ ] Delete job

#### Rate Limiting
- [ ] 60 requests/minute limit
- [ ] 1000 requests/hour limit
- [ ] Proper 429 response with Retry-After

#### File Validation
- [ ] PDF signature validation
- [ ] Image signature validation
- [ ] 50MB size limit
- [ ] Empty file rejection

#### Cleanup
- [ ] Automatic cleanup after 30 min
- [ ] Manual cleanup trigger
- [ ] Storage usage monitoring

#### Performance
- [ ] Response time < 500ms for simple ops
- [ ] Large file processing < 30s
- [ ] Memory usage stable

## Cross-Device Testing

### Desktop Browsers
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Edge (latest)
- [ ] Safari (latest)

### Mobile Browsers
- [ ] iOS Safari (iPhone)
- [ ] Android Chrome
- [ ] iOS Safari (iPad)
- [ ] Android Tablet

### PWA Testing
- [ ] Install prompt appears
- [ ] Works offline (shell only)
- [ ] Standalone display mode
- [ ] Icon display correct

### Responsive Testing
- [ ] 320px (mobile)
- [ ] 768px (tablet)
- [ ] 1024px (laptop)
- [ ] 1440px (desktop)
- [ ] 1920px (large desktop)

## Load Testing

### Concurrent Users
- [ ] 10 concurrent uploads
- [ ] 50 concurrent status checks
- [ ] 5 concurrent large file processing

### Large Files
- [ ] 10MB PDF processing
- [ ] 25MB PDF processing
- [ ] 50MB PDF (max limit)

## Error Handling
- [ ] Network interruption during upload
- [ ] Backend restart during processing
- [ ] Expired download token
- [ ] Invalid file type
- [ ] Corrupted upload

## Security Testing
- [ ] Path traversal attempts
- [ ] Oversized file upload
- [ ] Malicious file content
- [ ] CORS configuration
- [ ] Security headers present

## Deployment Testing

### Docker
- [ ] docker-compose up builds successfully
- [ ] Backend health check passes
- [ ] Frontend loads through nginx
- [ ] API proxy works

### Vercel (Frontend)
- [ ] Build succeeds
- [ ] API rewrites work
- [ ] PWA manifest served
- [ ] Security headers present

### Render (Backend)
- [ ] Docker build succeeds
- [ ] Health check passes
- [ ] Environment variables set
- [ ] Auto-deploy works

## Acceptance Criteria

All tests must pass before release:
- [ ] 0 critical bugs
- [ ] 0 high severity bugs
- [ ] < 5 medium severity bugs
- [ ] Performance targets met
- [ ] Security scan clean
- [ ] Cross-device compatibility verified