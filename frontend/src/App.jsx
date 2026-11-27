import React, { useState } from 'react'
import {
  Download,
  FileArchive,
  FileText,
  Image,
  Lock,
  Unlock,
  Merge,
  Scissors,
  RotateCw,
  Minimize2,
  ShieldCheck,
  ScanText,
  Layers,
  Wrench,
  Search,
  Info,
  FileImage,
  FileSpreadsheet,
  Presentation,
  Type,
  Droplets,
  Hash,
  PenTool,
  Highlighter,
  EyeOff,
  GitCompare,
  Moon,
  Sun,
} from 'lucide-react'
import ImageCompressor from './components/ImageCompressor'

const tools = [
  { id: 'merge', name: 'Merge PDF', description: 'Combine PDFs', icon: Merge },
  { id: 'split', name: 'Split PDF', description: 'Separate pages', icon: Scissors },
  { id: 'rotate', name: 'Rotate PDF', description: 'Rotate all pages', icon: RotateCw },
  { id: 'compress', name: 'Compress PDF', description: 'Reduce file size', icon: Minimize2 },
  { id: 'image-compressor', name: 'Image Compressor', description: 'Compress JPG, PNG & WebP', icon: FileImage },
  { id: 'protect', name: 'Protect PDF', description: 'Add a password', icon: Lock },
  { id: 'unlock', name: 'Unlock PDF', description: 'Remove a password', icon: Unlock },
  { id: 'ocr', name: 'OCR PDF', description: 'Recognize text', icon: ScanText },
  { id: 'organize', name: 'Organize Pages', description: 'Reorder or remove pages', icon: Layers },
  { id: 'repair', name: 'Repair PDF', description: 'Recover PDF structure', icon: Wrench },
  { id: 'extract-text', name: 'Extract Text', description: 'Save text from PDF', icon: FileText },
  { id: 'extract-images', name: 'Extract Images', description: 'Get embedded images', icon: Image },
  { id: 'metadata', name: 'PDF Metadata', description: 'Inspect document data', icon: Info },
  { id: 'preview', name: 'Page Preview', description: 'Generate previews', icon: FileImage },
  { id: 'to-word', name: 'PDF to Word', description: 'Convert to DOCX', icon: FileText },
  { id: 'to-jpg', name: 'PDF to JPG', description: 'Convert pages to JPG', icon: FileImage },
  { id: 'jpg-to-pdf', name: 'JPG to PDF', description: 'Convert images', icon: Image },
  { id: 'to-excel', name: 'PDF to Excel', description: 'Convert to XLSX', icon: FileSpreadsheet },
  { id: 'excel-to-pdf', name: 'Excel to PDF', description: 'Convert to PDF', icon: FileSpreadsheet },
  { id: 'to-powerpoint', name: 'PDF to PowerPoint', description: 'Convert to PPTX', icon: Presentation },
  { id: 'powerpoint-to-pdf', name: 'PowerPoint to PDF', description: 'Convert to PDF', icon: Presentation },
  { id: 'redact', name: 'Redact PDF', description: 'Remove selected content', icon: EyeOff },
  { id: 'compare', name: 'Compare PDFs', description: 'Compare two PDFs', icon: GitCompare },
  { id: 'add-text', name: 'Add Text', description: 'Add text to pages', icon: Type },
  { id: 'add-watermark', name: 'Add Watermark', description: 'Stamp pages', icon: Droplets },
  { id: 'add-page-numbers', name: 'Add Page Numbers', description: 'Number pages', icon: Hash },
  { id: 'add-signature', name: 'Add Signature', description: 'Sign a PDF', icon: PenTool },
  { id: 'add-annotation', name: 'Add Annotation', description: 'Annotate pages', icon: Highlighter },
]

export default function App() {
  const [selectedTool, setSelectedTool] = useState(null)
  const [dark, setDark] = useState(false)

  return (
    <div className={dark ? 'dark' : ''}>
      <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
        <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
            <button onClick={() => setSelectedTool(null)} className="flex items-center gap-2 font-bold text-blue-700 dark:text-blue-400">
              <FileArchive className="h-6 w-6" />
              PDF Master
            </button>
            <button
              type="button"
              onClick={() => setDark((value) => !value)}
              className="rounded-lg border border-slate-200 p-2 dark:border-slate-700"
              aria-label="Toggle theme"
            >
              {dark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
          </div>
        </header>

        <main className="mx-auto max-w-7xl px-4 py-8">
          {selectedTool ? (
            selectedTool.id === 'image-compressor'
              ? <ImageCompressor onBack={() => setSelectedTool(null)} />
              : <ToolWorkspace tool={selectedTool} onBack={() => setSelectedTool(null)} />
          ) : (
            <>
              <div className="mb-8">
                <h1 className="text-3xl font-bold md:text-4xl">Everything You Need to Work with PDFs</h1>
                <p className="mt-2 text-slate-600 dark:text-slate-300">Select a tool and process documents locally.</p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {tools.map((tool) => {
                  const Icon = tool.icon
                  return (
                    <button
                      key={tool.id}
                      type="button"
                      onClick={() => setSelectedTool(tool)}
                      className="rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-blue-400 hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
                    >
                      <Icon className="mb-4 h-7 w-7 text-blue-600" />
                      <div className="font-semibold">{tool.name}</div>
                      <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">{tool.description}</div>
                    </button>
                  )
                })}
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  )
}

function ToolWorkspace({ tool, onBack }) {
  const [files, setFiles] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [downloadUrl, setDownloadUrl] = useState('')
  const [angle, setAngle] = useState('90')
  const [password, setPassword] = useState('')

  const accepts = tool.id === 'jpg-to-pdf' || tool.id === 'excel-to-pdf' || tool.id === 'powerpoint-to-pdf'
    ? tool.id === 'jpg-to-pdf' ? 'image/jpeg,image/png'
      : tool.id === 'excel-to-pdf' ? '.xls,.xlsx'
      : '.ppt,.pptx'
    : tool.id === 'compare' ? '.pdf'
    : '.pdf'

  async function processFiles() {
    if (!files.length) {
      setError('Select at least one file.')
      return
    }

    setBusy(true)
    setError('')
    setDownloadUrl('')

    try {
      const form = new FormData()
      if (tool.id === 'merge') {
        files.forEach((file) => form.append('files', file))
      } else {
        form.append('file', files[0])
      }
      if (tool.id === 'rotate') form.append('angle', angle)
      if (tool.id === 'protect' || tool.id === 'unlock') form.append('password', password)

      const endpoint = tool.id === 'merge' ? '/api/pdf/merge'
        : tool.id === 'split' ? '/api/pdf/split'
        : tool.id === 'rotate' ? '/api/pdf/rotate'
        : tool.id === 'compress' ? '/api/pdf/compress'
        : tool.id === 'protect' ? '/api/pdf/protect'
        : tool.id === 'unlock' ? '/api/pdf/unlock'
        : tool.id === 'ocr' ? '/api/pdf/ocr'
        : tool.id === 'organize' ? '/api/pdf/organize'
        : tool.id === 'repair' ? '/api/pdf/repair'
        : tool.id === 'extract-text' ? '/api/pdf/extract-text'
        : tool.id === 'extract-images' ? '/api/pdf/extract-images'
        : tool.id === 'metadata' ? '/api/pdf/metadata'
        : tool.id === 'preview' ? '/api/pdf/preview'
        : tool.id === 'jpg-to-pdf' ? '/api/jpg-to-pdf'
        : tool.id === 'excel-to-pdf' ? '/api/excel-to-pdf'
        : tool.id === 'powerpoint-to-pdf' ? '/api/powerpoint-to-pdf'
        : `/api/pdf/${tool.id}`

      const response = await fetch(endpoint, { method: 'POST', body: form })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Processing failed')

      let jobId = data.job_id
      if (!jobId) throw new Error('The server did not return a job ID.')

      for (let attempt = 0; attempt < 60; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 500))
        const statusResponse = await fetch(`/api/jobs/${jobId}`)
        const status = await statusResponse.json()
        if (!statusResponse.ok) throw new Error(status.detail || 'Could not read job status')
        if (status.status === 'completed') {
          const url = `/api/jobs/${jobId}/download${data.download_token ? `?token=${encodeURIComponent(data.download_token)}` : ''}`
          setDownloadUrl(url)
          return
        }
        if (status.status === 'failed') throw new Error(status.error_message || 'Processing failed')
      }
      throw new Error('Processing timed out.')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="mx-auto max-w-2xl">
      <button type="button" onClick={onBack} className="mb-6 text-sm font-medium text-blue-700 hover:underline dark:text-blue-400">
        &larr; All tools
      </button>
      <h1 className="text-3xl font-bold">{tool.name}</h1>
      <p className="mt-2 text-slate-600 dark:text-slate-300">{tool.description}</p>

      <div className="mt-6 rounded-xl border-2 border-dashed border-slate-300 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
        <input
          type="file"
          accept={accepts}
          multiple={tool.id === 'merge'}
          onChange={(event) => setFiles(Array.from(event.target.files || []))}
          className="block w-full text-sm"
        />
        {files.length > 0 && (
          <ul className="mt-3 space-y-1 text-sm text-slate-600 dark:text-slate-300">
            {files.map((file) => <li key={`${file.name}-${file.size}`}>{file.name}</li>)}
          </ul>
        )}

        {tool.id === 'rotate' && (
          <label className="mt-4 block text-sm font-medium">
            Rotation
            <select value={angle} onChange={(event) => setAngle(event.target.value)} className="mt-1 block rounded border border-slate-300 px-3 py-2 dark:bg-slate-800">
              <option value="90">90 degrees clockwise</option>
              <option value="180">180 degrees</option>
              <option value="270">270 degrees clockwise</option>
            </select>
          </label>
        )}
        {(tool.id === 'protect' || tool.id === 'unlock') && (
          <label className="mt-4 block text-sm font-medium">
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 dark:bg-slate-800" />
          </label>
        )}

        <button
          type="button"
          onClick={processFiles}
          disabled={busy}
          className="mt-5 w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white disabled:opacity-50"
        >
          {busy ? 'Processing...' : `Process ${tool.name}`}
        </button>
      </div>

      {error && <div className="mt-4 rounded-lg border border-red-300 bg-red-50 p-4 text-red-700 dark:bg-red-950">{error}</div>}
      {downloadUrl && (
        <a
          href={downloadUrl}
          download
          className="mt-4 flex items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-3 font-semibold text-white"
        >
          <Download className="h-5 w-5" />
          Download result
        </a>
      )}
    </section>
  )
}
