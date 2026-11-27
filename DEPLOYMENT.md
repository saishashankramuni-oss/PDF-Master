# PDF Master - Deployment Guide

This guide covers deploying the PDF Master application to **Vercel (Frontend)** and **Render (Backend)**.

## Prerequisites

- GitHub account with the repository pushed
- Vercel account (free tier works)
- Render account (free tier works)
- Domain name (optional, for custom domains)

---

## Backend Deployment (Render)

### Render Blueprint (Recommended)

The repository-root `render.yaml` defines the backend service on branch `main`.
Connect this repository to Render and apply the Blueprint. It configures:

- Dockerfile: `backend/Dockerfile`
- Docker context: repository root (`.`), required by the Dockerfile's `COPY backend/...` commands
- Health check: `/health`
- `MAX_FILE_SIZE_MB`, `JOB_RETENTION_MINUTES`, `LOG_LEVEL`, and `ALLOWED_ORIGINS`

Render supplies the runtime `PORT`; do not set it to a fixed value in the service
environment. The container binds Uvicorn to `0.0.0.0` and uses that assigned port.
The configured frontend origin is `https://pdf-master.vercel.app`.

### Verify Backend Deployment

```bash
# Test health endpoint
curl https://your-backend.onrender.com/health

# Test API docs
open https://your-backend.onrender.com/docs

# Test the OpenAPI specification
curl https://your-backend.onrender.com/openapi.json
```

---

## Frontend Deployment (Vercel)

### Option 1: Vercel Dashboard (Recommended)

1. **Import Project on Vercel**
   - Go to https://vercel.com/new
   - Import your GitHub repository
   - Select the repository

2. **Configure Build Settings**
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm ci`
   - The `frontend/vercel.json` API rewrites send `/api/*` requests to the configured Render backend.

3. **Deploy**
   - Click "Deploy"
   - Wait for build (2-3 minutes)
   - Note your frontend URL: `https://pdf-master.vercel.app`

### Option 2: Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy from frontend directory
cd frontend
vercel --prod
```

### Configure Vercel Rewrites (for API proxy)

The `frontend/vercel.json` file proxies API requests to the backend. If the Render
URL changes:

1. Edit `frontend/vercel.json`
2. Update the rewrite destination:
   ```json
   {
     "rewrites": [
       {
         "source": "/api/(.*)",
         "destination": "https://YOUR-BACKEND-URL.onrender.com/api/$1"
       }
     ]
   }
   ```
3. Redeploy: `vercel --prod`

---

## Connect Frontend to Backend

After both deployments are complete:

1. **Update Backend CORS**
   - In Render dashboard → Environment Variables
   - Update `ALLOWED_ORIGINS`:
     ```
     ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://www.yourdomain.com
     ```
   - Redeploy backend

2. **Verify Connection**
   - Open frontend URL
   - Try uploading a PDF
   - Check browser dev tools for API calls

---

## Custom Domain (Optional)

### Frontend (Vercel)
1. Vercel Dashboard → Project → Settings → Domains
2. Add your domain (e.g., `pdf.example.com`)
3. Configure DNS records as instructed

### Backend (Render)
1. Render Dashboard → Service → Settings → Custom Domains
2. Add subdomain (e.g., `api.example.com`)
3. Update the frontend API rewrite destination to use the custom domain
4. Update backend `ALLOWED_ORIGINS` to include custom domain

---

## Post-Deployment Verification

### Automated Health Checks
```bash
# Backend
curl -f https://your-backend.onrender.com/health

# Frontend
curl -f https://your-frontend.vercel.app/

# API connectivity
curl -f https://your-frontend.vercel.app/api/tools
```

### Manual Testing Checklist
- [ ] Homepage loads correctly
- [ ] Theme toggle works (light/dark)
- [ ] PWA install prompt appears
- [ ] Upload a test PDF (1-2 MB)
- [ ] Process with "Compress PDF" tool
- [ ] Download result works
- [ ] Try 2-3 different tools
- [ ] Test on mobile browser
- [ ] Test PWA installation

### Monitoring Setup
1. **Render**: Built-in metrics (CPU, Memory, Requests)
2. **Vercel**: Built-in analytics
3. **Custom**: Application exposes:
   - `GET /api/performance/stats`
   - `GET /api/performance/system`
   - `GET /api/storage/usage`

---

## Troubleshooting

### Backend Issues

| Issue | Solution |
|-------|----------|
| Build fails | Check Render logs for missing dependencies |
| Health check fails | Verify `/health` endpoint returns 200 |
| CORS errors | Update `ALLOWED_ORIGINS` with frontend URL |
| File upload fails | Check `MAX_FILE_SIZE_MB` and memory limits |
| OCR not working | Tesseract not in PATH (falls back gracefully) |

### Frontend Issues

| Issue | Solution |
|-------|----------|
| API calls fail | Check the backend URL in `frontend/vercel.json` and the Render service status |
| PWA not installing | Verify `manifest.json` served correctly |
| Styles broken | Check Tailwind CDN or build output |
| API proxy 404 | Update `vercel.json` rewrite destination |

### Common Fixes

```bash
# Clear Vercel cache
vercel --prod --force

# Check Render logs
render logs your-service-name

# Test API directly
curl -X POST https://backend.onrender.com/api/pdf/compress \
  -F "file=@test.pdf"
```

---

## Cost Optimization

### Free Tier Limits
| Platform | Limits |
|----------|--------|
| **Render** | 750 hours/month, 512MB RAM, spins down after 15 min inactivity |
| **Vercel** | 100GB bandwidth, unlimited personal projects |

### Production Recommendations
1. **Upgrade Render** to Standard ($7/mo) for:
   - No spin-down
   - 1GB RAM, 1 CPU
   - Custom domains included

2. **Enable Vercel Pro** ($20/mo) for:
   - Team collaboration
   - Analytics
   - Password protection

3. **Add Redis** (for scaling):
   - Render Redis addon or Upstash
   - Update backend to use Redis for job queue

---

## Security Checklist

- [ ] `ALLOWED_ORIGINS` only includes your domains
- [ ] HTTPS enforced (automatic on both platforms)
- [ ] Security headers present (CSP, HSTS, etc.)
- [ ] Rate limiting active (60/min, 1000/hour)
- [ ] File validation working (magic bytes, size)
- [ ] Auto-cleanup running (30 min retention)
- [ ] No sensitive data in logs
- [ ] Error messages don't leak stack traces

---

## Rollback Procedure

### Vercel (Frontend)
```bash
# List deployments
vercel ls

# Rollback to previous
vercel rollback [deployment-url]
```

### Render (Backend)
1. Dashboard → Service → Deploys
2. Click "..." on previous successful deploy
3. Select "Rollback to this deploy"

---

## Support Contacts

- **Render Support**: support@render.com
- **Vercel Support**: support@vercel.com
- **Application Issues**: GitHub Issues in your repository

---

## Next Steps After Deployment

1. **Set up monitoring alerts** (Render metrics, Vercel analytics)
2. **Configure custom domain** if needed
3. **Add error tracking** (Sentry, LogRocket)
4. **Set up CI/CD** for automatic deployments
5. **Load test** with tools like k6 or Artillery
6. **Document API** for external consumers