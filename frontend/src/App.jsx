import React, { useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowLeft,
  CheckCircle2,
  Download,
  FileArchive,
  FileImage,
  FileSpreadsheet,
  FileText,
  GitCompare,
  Hash,
  Highlighter,
  Image,
  Info,
  Layers,
  Loader2,
  Lock,
  Minimize2,
  Moon,
  PenTool,
  Presentation,
  RotateCw,
  ScanText,
  Scissors,
  Search,
  ShieldCheck,
  Sun,
  Type,
  Upload,
  Unlock,
  Wrench,
  X,
  Droplets,
} from 'lucide-react'
import ImageCompressor from './components/ImageCompressor'
import { apiUrl } from './api'

const tools = [
  { id: 'merge', name: 'Merge PDF', description: 'Combine multiple PDFs into one', category: 'Organize', icon: FileArchive },
  { id: 'split', name: 'Split PDF', description: 'Split a document into separate pages', category: 'Organize', icon: Scissors },
  { id: 'rotate', name: 'Rotate PDF', description: 'Rotate every page in your document', category: 'Organize', icon: RotateCw },
  { id: 'organize', name: 'Organize Pages', description: 'Reorder, move, copy, remove, or extract pages', category: 'Organize', icon: Layers },
  { id: 'compress', name: 'Compress PDF', description: 'Reduce PDF size with measured output', category: 'Optimize', icon: Minimize2 },
  { id: 'repair', name: 'Repair PDF', description: 'Re-save a readable PDF to repair its structure', category: 'Optimize', icon: Wrench },
  { id: 'protect', name: 'Protect PDF', description: 'Encrypt a PDF with a password', category: 'Security', icon: Lock },
  { id: 'unlock', name: 'Unlock PDF', description: 'Remove a password from a PDF you can open', category: 'Security', icon: Unlock },
  { id: 'to-word', name: 'PDF to Word', description: 'Convert a PDF into a DOCX document', category: 'Convert', icon: FileText },
  { id: 'to-jpg', name: 'PDF to JPG', description: 'Export PDF pages as JPG images', category: 'Convert', icon: FileImage },
  { id: 'jpg-to-pdf', name: 'JPG to PDF', description: 'Create a PDF from images', category: 'Convert', icon: Image },
  { id: 'to-excel', name: 'PDF to Excel', description: 'Convert a PDF into an XLSX workbook', category: 'Convert', icon: FileSpreadsheet },
  { id: 'excel-to-pdf', name: 'Excel to PDF', description: 'Convert an Excel workbook into PDF', category: 'Convert', icon: FileSpreadsheet },
  { id: 'to-powerpoint', name: 'PDF to PowerPoint', description: 'Convert a PDF into a PPTX presentation', category: 'Convert', icon: Presentation },
  { id: 'powerpoint-to-pdf', name: 'PowerPoint to PDF', description: 'Convert a PowerPoint presentation into PDF', category: 'Convert', icon: Presentation },
  { id: 'add-text', name: 'Add Text', description: 'Place text on a selected PDF page', category: 'Edit', icon: Type },
  { id: 'add-image', name: 'Add Image', description: 'Place an image on a PDF page', category: 'Edit', icon: Image },
  { id: 'add-watermark', name: 'Add Watermark', description: 'Stamp selected pages with text', category: 'Edit', icon: Droplets },
  { id: 'add-page-numbers', name: 'Add Page Numbers', description: 'Number the pages in your PDF', category: 'Edit', icon: Hash },
  { id: 'add-signature', name: 'Add Signature', description: 'Place a signature image on a page', category: 'Edit', icon: PenTool },
  { id: 'add-annotation', name: 'Add Annotation', description: 'Add a highlight or shape annotation', category: 'Edit', icon: Highlighter },
  { id: 'ocr', name: 'OCR PDF', description: 'Recognize text in scanned pages with Tesseract', category: 'Advanced', icon: ScanText },
  { id: 'redact', name: 'Redact PDF', description: 'Permanently remove content in a page area', category: 'Advanced', icon: ShieldCheck },
  { id: 'compare', name: 'Compare PDFs', description: 'Compare text content in two PDFs', category: 'Advanced', icon: GitCompare },
  { id: 'extract-text', name: 'Extract Text', description: 'Export searchable text from a PDF', category: 'Advanced', icon: FileText },
  { id: 'extract-images', name: 'Extract Images', description: 'Download images embedded in a PDF', category: 'Advanced', icon: Image },
  { id: 'metadata', name: 'PDF Metadata', description: 'Read document properties and page sizes', category: 'Advanced', icon: Info },
  { id: 'preview', name: 'Page Preview', description: 'Create image previews of PDF pages', category: 'Advanced', icon: FileImage },
  { id: 'image-compressor', name: 'Image Compressor', description: 'Compress JPG, PNG, and WebP in your browser', category: 'Images', icon: FileImage },
]

const endpoints = {
  merge: '/api/pdf/merge',
  split: '/api/pdf/split',
  rotate: '/api/pdf/rotate',
  compress: '/api/pdf/compress',
  organize: '/api/pdf/organize',
  protect: '/api/pdf/protect',
  unlock: '/api/pdf/unlock',
  repair: '/api/pdf/repair',
  ocr: '/api/pdf/ocr',
  'to-word': '/api/pdf/to-word',
  'to-jpg': '/api/pdf/to-jpg',
  'jpg-to-pdf': '/api/jpg-to-pdf',
  'to-excel': '/api/pdf/to-excel',
  'excel-to-pdf': '/api/excel-to-pdf',
  'to-powerpoint': '/api/pdf/to-powerpoint',
  'powerpoint-to-pdf': '/api/powerpoint-to-pdf',
  'add-text': '/api/pdf/add-text',
  'add-image': '/api/pdf/add-image',
  'add-watermark': '/api/pdf/add-watermark',
  'add-page-numbers': '/api/pdf/add-page-numbers',
  'add-signature': '/api/pdf/add-signature',
  'add-annotation': '/api/pdf/add-annotation',
  redact: '/api/pdf/redact',
  compare: '/api/pdf/compare',
  'extract-text': '/api/pdf/extract-text',
  'extract-images': '/api/pdf/extract-images',
  metadata: '/api/pdf/metadata',
  preview: '/api/pdf/preview',
}

const categories = ['All tools', 'Organize', 'Optimize', 'Security', 'Convert', 'Edit', 'Advanced', 'Images']
const MAX_FILE_SIZE = 50 * 1024 * 1024

const defaultsByTool = {
  split: { page_numbers: '' },
  rotate: { angle: '90' },
  compress: { quality: 'medium' },
  organize: { operation: 'remove', pages: '', new_order: '', from_page: '1', to_page: '1' },
  protect: { password: '', owner_password: '' },
  unlock: { password: '' },
  repair: { aggressive: false },
  ocr: { language: 'eng', dpi: '300' },
  'to-jpg': { dpi: '150' },
  'add-text': { page_number: '1', x: '72', y: '72', text: '', font_size: '12', font_name: 'helv', color: '0,0,0', rotation: '0' },
  'add-image': { page_number: '1', x: '72', y: '72', width: '120', height: '90', keep_aspect_ratio: true },
  'add-watermark': { watermark_text: 'CONFIDENTIAL', font_size: '48', color: '0.5,0.5,0.5', opacity: '0.3', rotation: '45', pages: '' },
  'add-page-numbers': { start_number: '1', format_string: '{page}/{total}', position: 'bottom-center', font_size: '10', font_name: 'helv', color: '0.3,0.3,0.3', pages: '' },
  'add-signature': { page_number: '1', x: '72', y: '72', width: '150', height: '75' },
  'add-annotation': { page_number: '1', annotation_type: 'highlight', x0: '', y0: '', x1: '', y1: '', content: '', color: '1,1,0', opacity: '0.5' },
  redact: { page: '', x0: '', y0: '', x1: '', y1: '' },
  compare: { diff_mode: 'text' },
  preview: { dpi: '96', max_pages: '20' },
}

function getToolFields(toolId, values) {
  const field = (name, label, type = 'text', options = {}) => ({ name, label, type, ...options })
  const pageNumber = field('page_number', 'Page number', 'number', { min: 1 })

  switch (toolId) {
    case 'split':
      return [field('page_numbers', 'Pages to keep (comma-separated)', 'text', { placeholder: 'For example: 1,3,5' })]
    case 'rotate':
      return [field('angle', 'Rotation', 'select', { options: [['90', '90° clockwise'], ['180', '180°'], ['270', '270° clockwise']] })]
    case 'compress':
      return [field('quality', 'Compression level', 'select', { options: [['low', 'Low'], ['medium', 'Medium'], ['high', 'High']] })]
    case 'organize': {
      const fields = [field('operation', 'Operation', 'select', { options: [['remove', 'Remove pages'], ['extract', 'Extract pages'], ['reorder', 'Reorder pages'], ['move', 'Move one page'], ['copy', 'Copy pages to a new PDF']] })]
      if (['remove', 'extract', 'copy'].includes(values.operation)) {
        fields.push(field('pages', 'Page numbers', 'text', { placeholder: 'For example: 1,3,5', required: true }))
      } else if (values.operation === 'reorder') {
        fields.push(field('new_order', 'New page order', 'text', { placeholder: 'For example: 2,1,3', required: true }))
      } else {
        fields.push(field('from_page', 'Move page number', 'number', { min: 1 }))
        fields.push(field('to_page', 'Move to position', 'number', { min: 1 }))
      }
      return fields
    }
    case 'protect':
      return [field('password', 'Password', 'password'), field('owner_password', 'Owner password (optional)', 'password', { required: false })]
    case 'unlock':
      return [field('password', 'PDF password', 'password', { required: false })]
    case 'repair':
      return [field('aggressive', 'Use aggressive repair', 'checkbox')]
    case 'ocr':
      return [field('language', 'Tesseract language code', 'text', { placeholder: 'eng' }), field('dpi', 'Resolution (DPI)', 'number', { min: 72, max: 600 })]
    case 'to-jpg':
      return [field('dpi', 'Image resolution (DPI)', 'number', { min: 72, max: 600 })]
    case 'add-text':
      return [pageNumber, field('x', 'X position (points)', 'number'), field('y', 'Y position (points)', 'number'), field('text', 'Text'), field('font_size', 'Font size', 'number', { min: 1 }), field('font_name', 'Font name'), field('color', 'Text color (R,G,B from 0 to 1)'), field('rotation', 'Rotation (degrees)', 'number')]
    case 'add-image':
      return [pageNumber, field('x', 'X position (points)', 'number'), field('y', 'Y position (points)', 'number'), field('width', 'Width (points)', 'number', { required: false, min: 1 }), field('height', 'Height (points)', 'number', { required: false, min: 1 }), field('keep_aspect_ratio', 'Maintain image aspect ratio', 'checkbox')]
    case 'add-watermark':
      return [field('watermark_text', 'Watermark text'), field('font_size', 'Font size', 'number', { min: 1 }), field('color', 'Color (R,G,B from 0 to 1)'), field('opacity', 'Opacity (0–1)', 'number', { min: 0, max: 1, step: 0.1 }), field('rotation', 'Rotation (degrees)', 'number'), field('pages', 'Pages (comma-separated; blank means all)', 'text', { required: false })]
    case 'add-page-numbers':
      return [field('start_number', 'Starting number', 'number', { min: 1 }), field('format_string', 'Format ({page} and {total} are supported)'), field('position', 'Position', 'select', { options: [['bottom-center', 'Bottom center'], ['bottom-left', 'Bottom left'], ['bottom-right', 'Bottom right'], ['top-center', 'Top center'], ['top-left', 'Top left'], ['top-right', 'Top right']] }), field('font_size', 'Font size', 'number', { min: 1 }), field('font_name', 'Font name'), field('color', 'Color (R,G,B from 0 to 1)'), field('pages', 'Pages (comma-separated; blank means all)', 'text', { required: false })]
    case 'add-signature':
      return [pageNumber, field('x', 'X position (points)', 'number'), field('y', 'Y position (points)', 'number'), field('width', 'Width (points)', 'number', { min: 1 }), field('height', 'Height (points)', 'number', { min: 1 })]
    case 'add-annotation':
      return [pageNumber, field('annotation_type', 'Annotation type', 'select', { options: [['highlight', 'Highlight'], ['underline', 'Underline'], ['strikeout', 'Strike out'], ['squiggly', 'Squiggly'], ['free_text', 'Free text'], ['square', 'Square'], ['circle', 'Circle'], ['line', 'Line']] }), field('x0', 'Left (points)', 'number'), field('y0', 'Top (points)', 'number'), field('x1', 'Right (points)', 'number'), field('y1', 'Bottom (points)', 'number'), field('content', 'Annotation text (for free text)', 'text', { required: false }), field('color', 'Color (R,G,B from 0 to 1)'), field('opacity', 'Opacity (0–1)', 'number', { min: 0, max: 1, step: 0.1 })]
    case 'redact':
      return [field('page', 'Page number', 'number', { min: 1 }), field('x0', 'Left (points)', 'number'), field('y0', 'Top (points)', 'number'), field('x1', 'Right (points)', 'number'), field('y1', 'Bottom (points)', 'number')]
    case 'compare':
      return [field('diff_mode', 'Comparison mode', 'select', { options: [['text', 'Text']] })]
    case 'preview':
      return [field('dpi', 'Preview resolution (DPI)', 'number', { min: 72, max: 300 }), field('max_pages', 'Maximum pages', 'number', { min: 1, max: 50 })]
    default:
      return []
  }
}

function acceptsForTool(toolId) {
  if (toolId === 'jpg-to-pdf') return '.jpg,.jpeg,.png'
  if (toolId === 'excel-to-pdf') return '.xls,.xlsx'
  if (toolId === 'powerpoint-to-pdf') return '.ppt,.pptx'
  return '.pdf'
}

function isPdfTool(toolId) {
  return !['jpg-to-pdf', 'excel-to-pdf', 'powerpoint-to-pdf'].includes(toolId)
}

function parsePageList(value, label) {
  const pages = value.split(',').map((part) => part.trim())
  if (!value.trim() || pages.some((page) => !/^\d+$/.test(page))) {
    throw new Error(`${label} must contain comma-separated positive page numbers.`)
  }
  return pages.map(Number)
}

async function getErrorMessage(response) {
  try {
    const data = await response.json()
    return data.detail || data.message || `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

function filenameFromHeader(header, fallback) {
  const encoded = header?.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
  if (encoded) {
    try {
      return decodeURIComponent(encoded)
    } catch {
      return fallback
    }
  }
  return header?.match(/filename="?([^";]+)"?/i)?.[1] || fallback
}

function fallbackFilename(toolId, contentType) {
  const mediaType = contentType.split(';')[0].trim().toLowerCase()
  const extensions = {
    'application/pdf': 'pdf',
    'application/zip': 'zip',
    'application/json': 'json',
    'text/plain': 'txt',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
    'image/jpeg': 'jpg',
    'image/png': 'png',
  }
  return `${toolId}-result.${extensions[mediaType] || 'bin'}`
}

function FormField({ field, value, onChange }) {
  const baseClass = 'mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:ring-blue-900'
  if (field.type === 'checkbox') {
    return (
      <label className="flex items-center gap-3 rounded-xl border border-slate-200 p-3 text-sm dark:border-slate-700">
        <input type="checkbox" checked={Boolean(value)} onChange={(event) => onChange(field.name, event.target.checked)} />
        {field.label}
      </label>
    )
  }
  return (
    <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
      {field.label}
      {field.type === 'select' ? (
        <select className={baseClass} value={value ?? ''} required={field.required !== false} onChange={(event) => onChange(field.name, event.target.value)}>
          {field.options.map(([option, label]) => <option key={option} value={option}>{label}</option>)}
        </select>
      ) : (
        <input
          className={baseClass}
          type={field.type || 'text'}
          value={value ?? ''}
          required={field.required !== false}
          placeholder={field.placeholder}
          min={field.min}
          max={field.max}
          step={field.step}
          onChange={(event) => onChange(field.name, event.target.value)}
        />
      )}
    </label>
  )
}

export default function App() {
  const [selectedTool, setSelectedTool] = useState(null)
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All tools')
  const [dark, setDark] = useState(false)

  const filteredTools = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    return tools.filter((tool) => {
      const matchesCategory = category === 'All tools' || tool.category === category
      const matchesQuery = !normalizedQuery
        || `${tool.name} ${tool.description} ${tool.category}`.toLowerCase().includes(normalizedQuery)
      return matchesCategory && matchesQuery
    })
  }, [category, query])

  function openTool(tool) {
    setSelectedTool(tool)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className={dark ? 'dark' : ''}>
      <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
            <button type="button" onClick={() => setSelectedTool(null)} className="flex shrink-0 items-center gap-2 font-bold text-slate-900 dark:text-white" aria-label="PDF Master home">
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-blue-600 text-white"><FileArchive className="h-5 w-5" /></span>
              <span className="text-lg">PDF Master</span>
            </button>
            <nav className="hidden items-center gap-6 text-sm font-medium text-slate-600 md:flex dark:text-slate-300" aria-label="Main navigation">
              <button type="button" onClick={() => { setSelectedTool(null); setCategory('All tools') }}>All tools</button>
              <button type="button" onClick={() => { setSelectedTool(null); setCategory('Organize') }}>Organize</button>
              <button type="button" onClick={() => { setSelectedTool(null); setCategory('Convert') }}>Convert</button>
              <button type="button" onClick={() => openTool(tools.find((tool) => tool.id === 'image-compressor'))}>Image compressor</button>
            </nav>
            <button
              type="button"
              onClick={() => setDark((value) => !value)}
              className="rounded-xl border border-slate-200 p-2 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-900"
              aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
            >
              {dark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
          </div>
        </header>

        <main className="mx-auto max-w-7xl px-4 pb-14 pt-8 sm:px-6 sm:pt-12">
          {selectedTool ? (
            selectedTool.id === 'image-compressor'
              ? <ImageCompressor onBack={() => setSelectedTool(null)} />
              : <ToolWorkspace tool={selectedTool} onBack={() => setSelectedTool(null)} />
          ) : (
            <>
              <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-700 via-blue-600 to-indigo-700 px-6 py-10 text-white shadow-xl sm:px-10 sm:py-14">
                <div className="absolute -right-10 -top-20 h-64 w-64 rounded-full border-[36px] border-white/10" aria-hidden="true" />
                <div className="relative max-w-3xl">
                  <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1.5 text-xs font-semibold tracking-wide">
                    <span className="h-2 w-2 rounded-full bg-emerald-300" /> PDF tools and browser-based image compression
                  </div>
                  <h1 className="text-3xl font-bold leading-tight sm:text-5xl">Everything you need to work with documents</h1>
                  <p className="mt-4 max-w-2xl text-sm leading-6 text-blue-100 sm:text-base">
                    Merge, convert, edit, and organize PDFs with clear controls. Compress images locally in your browser without uploading them.
                  </p>
                  <label className="mt-7 flex max-w-xl items-center gap-3 rounded-2xl bg-white px-4 py-3 text-slate-500 shadow-lg">
                    <Search className="h-5 w-5 shrink-0" />
                    <input
                      type="search"
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      placeholder="Search PDF tools..."
                      aria-label="Search tools"
                      className="w-full bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400"
                    />
                    <span className="hidden rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-500 sm:inline">Search</span>
                  </label>
                </div>
              </section>

              <section className="mt-6 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-900 sm:grid-cols-2 sm:p-5">
                <div className="flex items-start gap-3">
                  <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
                  <p><strong>PDF privacy:</strong> PDF files are sent over HTTPS to the PDF Master backend and automatically cleaned up after the retention window.</p>
                </div>
                <div className="flex items-start gap-3">
                  <FileImage className="mt-0.5 h-5 w-5 shrink-0 text-blue-600" />
                  <p><strong>Image privacy:</strong> Image Compressor runs in your browser; images are not sent to the backend.</p>
                </div>
              </section>

              <section className="mt-9" aria-labelledby="tools-heading">
                <div className="flex flex-wrap items-end justify-between gap-3">
                  <div>
                    <h2 id="tools-heading" className="text-2xl font-bold">Choose a tool</h2>
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{filteredTools.length} tools available</p>
                  </div>
                  <button type="button" onClick={() => { setQuery(''); setCategory('All tools') }} className="text-sm font-semibold text-blue-700 hover:underline dark:text-blue-400">
                    Clear filters
                  </button>
                </div>
                <div className="mt-5 flex gap-2 overflow-x-auto pb-2" role="group" aria-label="Filter by category">
                  {categories.map((item) => (
                    <button
                      key={item}
                      type="button"
                      onClick={() => setCategory(item)}
                      aria-pressed={category === item}
                      className={`shrink-0 rounded-full px-4 py-2 text-sm font-medium transition ${category === item ? 'bg-blue-600 text-white' : 'border border-slate-200 bg-white text-slate-600 hover:border-blue-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300'}`}
                    >
                      {item}
                    </button>
                  ))}
                </div>
                {filteredTools.length ? (
                  <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    {filteredTools.map((tool) => {
                      const Icon = tool.icon
                      return (
                        <button
                          key={tool.id}
                          type="button"
                          onClick={() => openTool(tool)}
                          className="group rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-lg focus-visible:outline-blue-600 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-blue-700"
                        >
                          <span className="mb-5 grid h-11 w-11 place-items-center rounded-xl bg-blue-50 text-blue-700 transition group-hover:bg-blue-600 group-hover:text-white dark:bg-blue-950 dark:text-blue-300">
                            <Icon className="h-5 w-5" />
                          </span>
                          <span className="block font-semibold">{tool.name}</span>
                          <span className="mt-1 block min-h-10 text-sm leading-5 text-slate-500 dark:text-slate-400">{tool.description}</span>
                          <span className="mt-4 block text-xs font-semibold uppercase tracking-wide text-blue-700 dark:text-blue-400">{tool.category}</span>
                        </button>
                      )
                    })}
                  </div>
                ) : (
                  <div className="mt-4 rounded-2xl border border-dashed border-slate-300 p-10 text-center dark:border-slate-700">
                    <p className="font-semibold">No matching tools</p>
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Try another search or category.</p>
                  </div>
                )}
              </section>
            </>
          )}
        </main>

        <footer className="border-t border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
          <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-6 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-6 dark:text-slate-400">
            <span className="font-semibold text-slate-700 dark:text-slate-200">PDF Master</span>
            <span>PDF files are processed by the configured backend. Image compression stays in your browser.</span>
          </div>
        </footer>
      </div>
    </div>
  )
}

function ToolWorkspace({ tool, onBack }) {
  const [files, setFiles] = useState([])
  const [extraFile, setExtraFile] = useState(null)
  const [values, setValues] = useState(() => ({ ...(defaultsByTool[tool.id] || {}) }))
  const [busy, setBusy] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState('')
  const [progressMessage, setProgressMessage] = useState('')
  const [downloadUrl, setDownloadUrl] = useState('')
  const [downloadName, setDownloadName] = useState('')
  const [downloadReady, setDownloadReady] = useState(false)
  const fileInputRef = useRef(null)
  const extraInputRef = useRef(null)
  const isMultiple = ['merge', 'compare', 'jpg-to-pdf'].includes(tool.id)
  const isImageUploadTool = tool.id === 'jpg-to-pdf'
  const minimumFileCount = ['merge', 'compare'].includes(tool.id) ? 2 : 1
  const fields = getToolFields(tool.id, values)

  useEffect(() => () => {
    if (downloadUrl) URL.revokeObjectURL(downloadUrl)
  }, [downloadUrl])

  function updateValue(name, value) {
    setValues((current) => ({ ...current, [name]: value }))
    setError('')
  }

  function acceptFiles(candidateList) {
    const candidates = Array.from(candidateList || [])
    const valid = []
    for (const file of candidates) {
      if (file.size > MAX_FILE_SIZE) {
        setError(`${file.name} is larger than the 50 MB per-file limit.`)
        continue
      }
      const extension = file.name.split('.').pop()?.toLowerCase() || ''
      const allowed = isImageUploadTool
        ? ['jpg', 'jpeg', 'png']
        : tool.id === 'excel-to-pdf'
          ? ['xls', 'xlsx']
          : tool.id === 'powerpoint-to-pdf'
            ? ['ppt', 'pptx']
            : ['pdf']
      if (!allowed.includes(extension)) {
        setError(`${file.name} is not a supported file type for ${tool.name}.`)
        continue
      }
      if (isPdfTool(tool.id) && file.type && file.type !== 'application/pdf') {
        setError(`${file.name} does not have a PDF MIME type.`)
        continue
      }
      valid.push(file)
    }
    setFiles((current) => {
      const next = isMultiple ? [...current, ...valid] : valid.slice(0, 1)
      const seen = new Set()
      return next.filter((file) => {
        const key = `${file.name}:${file.size}:${file.lastModified}`
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })
    })
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  function removeFile(index) {
    setFiles((current) => current.filter((_, fileIndex) => fileIndex !== index))
  }

  function appendToolOptions(form) {
    if (tool.id === 'organize') {
      const operation = values.operation
      let pageData
      if (['remove', 'extract', 'copy'].includes(operation)) {
        pageData = { pages: parsePageList(values.pages, 'Page numbers') }
      } else if (operation === 'reorder') {
        pageData = { new_order: parsePageList(values.new_order, 'New page order') }
      } else {
        pageData = { from_page: Number(values.from_page), to_page: Number(values.to_page) }
        if (!Number.isInteger(pageData.from_page) || !Number.isInteger(pageData.to_page) || pageData.from_page < 1 || pageData.to_page < 1) {
          throw new Error('Move positions must be positive whole page numbers.')
        }
      }
      form.append('operation', operation)
      form.append('page_data', JSON.stringify(pageData))
      return
    }

    if (tool.id === 'redact') {
      const redaction = {
        page: Number(values.page),
        x0: Number(values.x0),
        y0: Number(values.y0),
        x1: Number(values.x1),
        y1: Number(values.y1),
      }
      if (!Number.isInteger(redaction.page) || redaction.page < 1
        || ![redaction.x0, redaction.y0, redaction.x1, redaction.y1].every(Number.isFinite)
        || redaction.x1 <= redaction.x0 || redaction.y1 <= redaction.y0) {
        throw new Error('Enter a page number and a rectangle with right/bottom coordinates larger than left/top.')
      }
      form.append('redactions', JSON.stringify([redaction]))
      return
    }

    fields.forEach((field) => {
      const value = values[field.name]
      if (value === undefined || value === null || value === '') {
        if (field.required === false) return
        if (field.type === 'checkbox') {
          form.append(field.name, 'false')
          return
        }
        throw new Error(`${field.label} is required.`)
      }
      if (field.type === 'number' && value !== '' && !Number.isFinite(Number(value))) {
        throw new Error(`${field.label} must be a valid number.`)
      }
      form.append(field.name, field.type === 'checkbox' ? String(Boolean(value)) : String(value ?? ''))
    })
  }

  async function processFiles() {
    if (busy) return
    setError('')
    setDownloadReady(false)
    setDownloadName('')
    if (downloadUrl) {
      URL.revokeObjectURL(downloadUrl)
      setDownloadUrl('')
    }
    if (tool.id === 'compare' && files.length !== 2) {
      setError('Select exactly two PDF files to compare.')
      return
    }
    if (files.length < minimumFileCount) {
      setError(minimumFileCount === 2 ? `Select at least ${minimumFileCount} files for this tool.` : 'Select a file before processing.')
      return
    }
    if (tool.id === 'add-image' || tool.id === 'add-signature') {
      if (!extraFile) {
        setError(tool.id === 'add-image' ? 'Select an image to add to the PDF.' : 'Select a signature image.')
        return
      }
      const extension = extraFile.name.split('.').pop()?.toLowerCase()
      if (!['jpg', 'jpeg', 'png'].includes(extension) || (extraFile.type && !['image/jpeg', 'image/png'].includes(extraFile.type))) {
        setError('Select a valid JPG or PNG image.')
        return
      }
      if (extraFile.size > MAX_FILE_SIZE) {
        setError('The selected image is larger than the 50 MB per-file limit.')
        return
      }
    }

    setBusy(true)
    setProgressMessage('Uploading files securely...')
    try {
      const form = new FormData()
      if (tool.id === 'merge' || tool.id === 'jpg-to-pdf') {
        files.forEach((file) => form.append('files', file))
      } else if (tool.id === 'compare') {
        form.append('file1', files[0])
        form.append('file2', files[1])
      } else {
        form.append('file', files[0])
      }
      if (tool.id === 'add-image') form.append('image', extraFile)
      if (tool.id === 'add-signature') form.append('signature', extraFile)
      appendToolOptions(form)

      const response = await fetch(apiUrl(endpoints[tool.id]), { method: 'POST', body: form })
      if (!response.ok) throw new Error(await getErrorMessage(response))
      const responseType = response.headers.get('content-type') || ''
      if (!responseType.includes('application/json')) {
        const blob = await response.blob()
        setDownloadUrl(URL.createObjectURL(blob))
        setDownloadName(filenameFromHeader(
          response.headers.get('content-disposition'),
          fallbackFilename(tool.id, responseType),
        ))
        setDownloadReady(true)
        setProgressMessage('Processing complete.')
        return
      }

      const job = await response.json()
      if (!job.job_id) throw new Error('The server did not return a processing job ID.')
      setProgressMessage('Processing your files...')
      let completedJob
      for (let attempt = 0; attempt < 600; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 500))
        const statusResponse = await fetch(apiUrl(`/api/jobs/${encodeURIComponent(job.job_id)}`))
        if (!statusResponse.ok) throw new Error(await getErrorMessage(statusResponse))
        const status = await statusResponse.json()
        if (status.status === 'failed') throw new Error(status.error_message || 'The server could not process these files.')
        if (status.status === 'completed') {
          completedJob = status
          break
        }
      }
      if (!completedJob) throw new Error('Processing took too long. Please try again with a smaller file.')

      const token = completedJob.download_token || job.download_token
      if (!token) throw new Error('The server completed the job but did not provide a secure download link.')
      setProgressMessage('Preparing your download...')
      const downloadPath = `/api/jobs/${encodeURIComponent(job.job_id)}/download?token=${encodeURIComponent(token)}`
      const downloadResponse = await fetch(apiUrl(downloadPath))
      if (!downloadResponse.ok) throw new Error(await getErrorMessage(downloadResponse))
      const blob = await downloadResponse.blob()
      setDownloadUrl(URL.createObjectURL(blob))
      setDownloadName(filenameFromHeader(
        downloadResponse.headers.get('content-disposition'),
        fallbackFilename(tool.id, downloadResponse.headers.get('content-type') || ''),
      ))
      setDownloadReady(true)
      setProgressMessage('Processing complete.')
    } catch (processingError) {
      setError(processingError.message || 'Processing failed. Please try again.')
      setProgressMessage('')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="mx-auto max-w-4xl">
      <button type="button" onClick={onBack} className="mb-6 inline-flex items-center gap-2 text-sm font-semibold text-blue-700 hover:underline dark:text-blue-400">
        <ArrowLeft className="h-4 w-4" /> All tools
      </button>
      <div className="mb-6">
        <div className="text-xs font-semibold uppercase tracking-wider text-blue-700 dark:text-blue-400">{tool.category}</div>
        <h1 className="mt-1 text-3xl font-bold">{tool.name}</h1>
        <p className="mt-2 text-slate-600 dark:text-slate-300">{tool.description}</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-5">
          <div
            onDragOver={(event) => { event.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => { event.preventDefault(); setDragging(false); acceptFiles(event.dataTransfer.files) }}
            className={`rounded-2xl border-2 border-dashed p-6 text-center transition sm:p-8 ${dragging ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/40' : 'border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-900'}`}
          >
            <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300"><Upload className="h-6 w-6" /></span>
            <h2 className="mt-4 font-semibold">Drop your {isImageUploadTool ? 'images' : 'file'} here</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Maximum 50 MB per file</p>
            <input ref={fileInputRef} className="sr-only" type="file" accept={acceptsForTool(tool.id)} multiple={isMultiple} onChange={(event) => acceptFiles(event.target.files)} />
            <button type="button" onClick={() => fileInputRef.current?.click()} className="mt-4 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700">
              Browse {isImageUploadTool ? 'images' : 'files'}
            </button>
          </div>

          {files.length > 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="font-semibold">Selected files ({files.length})</h2>
                <button type="button" onClick={() => setFiles([])} disabled={busy} className="text-xs font-semibold text-slate-500 hover:text-red-600 disabled:opacity-50">Remove all</button>
              </div>
              <ul className="space-y-2">
                {files.map((file, index) => (
                  <li key={`${file.name}:${file.size}:${file.lastModified}`} className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2.5 dark:bg-slate-800">
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-medium">{file.name}</span>
                      <span className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                    </span>
                    <button type="button" onClick={() => removeFile(index)} disabled={busy} aria-label={`Remove ${file.name}`} className="rounded-lg p-2 text-slate-500 hover:bg-white hover:text-red-600 disabled:opacity-50 dark:hover:bg-slate-700">
                      <X className="h-4 w-4" />
                    </button>
                  </li>
                ))}
              </ul>
              {tool.id === 'compare' && <p className="mt-2 text-xs text-slate-500">The first selected PDF is compared with the second.</p>}
            </div>
          )}

          {(tool.id === 'add-image' || tool.id === 'add-signature') && (
            <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
              <h2 className="font-semibold">{tool.id === 'add-image' ? 'Image to place' : 'Signature image'}</h2>
              <input ref={extraInputRef} className="mt-3 block w-full text-sm" type="file" accept=".jpg,.jpeg,.png" onChange={(event) => setExtraFile(event.target.files?.[0] || null)} />
              {extraFile && <p className="mt-2 truncate text-xs text-slate-500">{extraFile.name}</p>}
            </div>
          )}

          {fields.length > 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900 sm:p-5">
              <h2 className="mb-4 font-semibold">Processing settings</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                {fields.map((field) => (
                  <div key={field.name} className={field.type === 'checkbox' ? 'sm:col-span-2' : ''}>
                    <FormField field={field} value={values[field.name]} onChange={updateValue} />
                  </div>
                ))}
              </div>
              {tool.id === 'redact' && <p className="mt-3 text-xs leading-5 text-amber-700 dark:text-amber-300">Coordinates are PDF points from the page’s top-left. Redaction permanently removes content inside the rectangle.</p>}
              {tool.id === 'organize' && <p className="mt-3 text-xs text-slate-500">Use comma-separated page numbers. Reorder requires the complete page order.</p>}
            </div>
          )}

          <button type="button" onClick={processFiles} disabled={busy} className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3.5 font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60">
            {busy ? <><Loader2 className="h-5 w-5 animate-spin" /> Processing...</> : <>Process {tool.name}</>}
          </button>

          {busy && (
            <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-900 dark:border-blue-900 dark:bg-blue-950 dark:text-blue-100" role="status" aria-live="polite">
              <div className="flex items-center gap-3"><Loader2 className="h-5 w-5 animate-spin" /><span>{progressMessage}</span></div>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-blue-200 dark:bg-blue-900"><div className="h-full w-1/3 animate-pulse rounded-full bg-blue-600" /></div>
            </div>
          )}
          {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">{error}</div>}
          {downloadReady && (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900 dark:bg-emerald-950">
              <div className="flex items-center gap-2 font-semibold text-emerald-800 dark:text-emerald-200"><CheckCircle2 className="h-5 w-5" /> Your file is ready</div>
              <p className="mt-1 truncate text-sm text-emerald-700 dark:text-emerald-300">{downloadName}</p>
              <a href={downloadUrl} download={downloadName} className="mt-4 flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 font-semibold text-white hover:bg-emerald-700">
                <Download className="h-5 w-5" /> Download result
              </a>
            </div>
          )}
        </div>

        <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="font-semibold">How it works</h2>
          <ol className="mt-4 space-y-4 text-sm text-slate-600 dark:text-slate-300">
            <li className="flex gap-3"><span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-blue-50 text-xs font-bold text-blue-700 dark:bg-blue-950 dark:text-blue-300">1</span><span>Select the required file or files and configure the options.</span></li>
            <li className="flex gap-3"><span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-blue-50 text-xs font-bold text-blue-700 dark:bg-blue-950 dark:text-blue-300">2</span><span>PDF tools send the files to the configured PDF Master API for processing.</span></li>
            <li className="flex gap-3"><span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-blue-50 text-xs font-bold text-blue-700 dark:bg-blue-950 dark:text-blue-300">3</span><span>Download the result when processing completes.</span></li>
          </ol>
          {tool.id === 'to-excel' || tool.id === 'excel-to-pdf' || tool.id === 'to-powerpoint' || tool.id === 'powerpoint-to-pdf' ? (
            <p className="mt-5 rounded-xl bg-amber-50 p-3 text-xs leading-5 text-amber-800 dark:bg-amber-950 dark:text-amber-200">Office conversion requires LibreOffice on the backend host. The service reports an error if it is unavailable.</p>
          ) : null}
          {tool.id === 'ocr' && <p className="mt-5 rounded-xl bg-amber-50 p-3 text-xs leading-5 text-amber-800 dark:bg-amber-950 dark:text-amber-200">Scanned pages require Tesseract and the selected language data to be installed on the backend.</p>}
        </aside>
      </div>
    </section>
  )
}
