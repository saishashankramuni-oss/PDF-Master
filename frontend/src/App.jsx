import React, { useMemo, useState } from 'react'
import { FileText, Upload, Download, RotateCw, Layers, Scissors, Minimize2, FileSearch, Info, LoaderCircle, CheckCircle2, AlertCircle } from 'lucide-react'

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

const TOOLS = [
  { id: 'merge', name: 'Merge PDF', description: 'Combine multiple PDF files', icon: Layers, multiple: true },
  { id: 'split', name: 'Split PDF', description: 'Extract every page into a ZIP', icon: Scissors },
  { id: 'rotate', name: 'Rotate PDF', description: 'Rotate all pages', icon: RotateCw },
  { id: 'compress', name: 'Compress PDF', description: 'Reduce PDF file size', icon: Minimize2 },
  { id: 'extract-text', name: 'Extract Text', description: 'Save searchable text as TXT', icon: FileSearch },
  { id: 'metadata', name: 'PDF Metadata', description: 'View document information as JSON', icon: Info },
]

export default function App() {
  const [toolId, setToolId] = useState('merge')
  const [files, setFiles] = useState([])
  const [angle, setAngle] = useState('90')
  const [quality, setQuality] = useState('medium')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [health, setHealth] = useState('unknown')

  const tool = useMemo(() => TOOLS.find(item => item.id === toolId) || TOOLS[0], [toolId])

  async function checkHealth() {
    try {
      const response = await fetch(API_BASE.replace(/\/api$/, '') + '/health')
      if (!response.ok) throw new Error('Backend health check failed')
      setHealth('online')
    } catch {
      setHealth('offline')
    }
  }

  function selectTool(id) {
    setToolId(id)
    setFiles([])
    setError('')
    setResult(null)
  }

  function handleFiles(event) {
    setFiles(Array.from(event.target.files || []))
    setError('')
    setResult(null)
  }

  async function processFiles(event) {
    event.preventDefault()
    if (!files.length) {
      setError('Please select a PDF file first.')
      return
    }
    if (files.some(file => file.size > 50 * 1024 * 1024)) {
      setError('Each PDF must be 50 MB or smaller.')
      return
    }
    setBusy(true)
    setError('')
    setResult(null)
    try {
      const body = new FormData()
      files.forEach(file => body.append('files', file))
      if (toolId === 'rotate') body.append('angle', angle)
      if (toolId === 'compress') body.append('quality', quality)
      const response = await fetch(`${API_BASE}/process/${toolId}`, { method: 'POST', body })
      if (!response.ok) {
        let message = 'Processing failed. Please try another PDF.'
        try {
          const data = await response.json()
          message = data.detail || message
        } catch {}
        throw new Error(message)
      }
      const blob = await response.blob()
      const disposition = response.headers.get('content-disposition') || ''
      const match = disposition.match(/filename="?([^";]+)"?/i)
      const filename = match?.[1] || `${toolId}-result`
      const url = URL.createObjectURL(blob)
      setResult({ url, filename, size: blob.size })
    } catch (err) {
      setError(err.message || 'Unable to connect to the PDF service.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-600 p-2 text-white"><FileText size={24} /></div>
            <div><div className="text-xl font-bold">PDF Master</div><div className="text-xs text-slate-500">Simple PDF tools, right in your browser</div></div>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className={`h-2.5 w-2.5 rounded-full ${health === 'online' ? 'bg-green-500' : health === 'offline' ? 'bg-red-500' : 'bg-slate-300'}`} />
            <span className="text-slate-600">{health === 'online' ? 'Service online' : health === 'offline' ? 'Service unavailable' : 'Service not checked'}</span>
            <button onClick={checkHealth} className="ml-2 rounded-lg border px-3 py-1.5 hover:bg-slate-50">Check</button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-10">
        <section className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">All your essential PDF tools</h1>
          <p className="mt-2 text-slate-600">Choose a tool, add your document, and download the processed result.</p>
        </section>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {TOOLS.map(item => {
            const Icon = item.icon
            const active = item.id === toolId
            return <button key={item.id} onClick={() => selectTool(item.id)} className={`rounded-xl border p-4 text-left transition hover:border-blue-400 hover:bg-blue-50 ${active ? 'border-blue-600 bg-blue-50 ring-1 ring-blue-600' : 'border-slate-200 bg-white'}`}>
              <div className="mb-3 inline-flex rounded-lg bg-white p-2 text-blue-700 shadow-sm"><Icon size={22} /></div>
              <div className="font-semibold">{item.name}</div>
              <div className="mt-1 text-sm text-slate-500">{item.description}</div>
            </button>
          })}
        </div>

        <form onSubmit={processFiles} className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3"><Upload className="text-blue-600" /><h2 className="text-xl font-semibold">{tool.name}</h2></div>
          <p className="mt-1 text-sm text-slate-500">{tool.multiple ? 'Select two or more PDFs to combine.' : 'Select one PDF file to continue.'}</p>
          <label className="mt-5 flex cursor-pointer flex-col items-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center hover:border-blue-400">
            <Upload size={30} className="mb-3 text-slate-400" />
            <span className="font-medium">Choose {tool.multiple ? 'PDF files' : 'a PDF file'}</span>
            <span className="mt-1 text-sm text-slate-500">PDF format · Maximum 50 MB per file</span>
            <input className="sr-only" type="file" accept="application/pdf,.pdf" multiple={!!tool.multiple} onChange={handleFiles} />
          </label>
          {files.length > 0 && <ul className="mt-4 space-y-2">{files.map((file, index) => <li key={index} className="flex justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm"><span className="truncate">{file.name}</span><span className="ml-3 shrink-0 text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</span></li>)}</ul>}
          {toolId === 'rotate' && <label className="mt-4 block text-sm font-medium">Rotation angle<select value={angle} onChange={e => setAngle(e.target.value)} className="mt-1 block w-full rounded-lg border border-slate-300 p-2"><option value="90">90° clockwise</option><option value="180">180°</option><option value="270">270° clockwise</option></select></label>}
          {toolId === 'compress' && <label className="mt-4 block text-sm font-medium">Compression level<select value={quality} onChange={e => setQuality(e.target.value)} className="mt-1 block w-full rounded-lg border border-slate-300 p-2"><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label>}
          {error && <div role="alert" className="mt-4 flex gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700"><AlertCircle size={18} className="shrink-0" />{error}</div>}
          {result && <div className="mt-4 flex flex-col gap-3 rounded-lg bg-green-50 p-4 text-green-800 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-2"><CheckCircle2 size={20} /><div><div className="font-semibold">Your file is ready</div><div className="text-sm">{result.filename} · {(result.size / 1024).toFixed(1)} KB</div></div></div><a href={result.url} download={result.filename} className="inline-flex items-center justify-center gap-2 rounded-lg bg-green-700 px-4 py-2 font-medium text-white hover:bg-green-800"><Download size={18} />Download</a></div>}
          <button disabled={busy || !files.length} className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50">{busy ? <><LoaderCircle className="animate-spin" size={19} />Processing...</> : 'Process PDF'}</button>
        </form>

        <p className="mt-6 text-center text-xs text-slate-500">Files are processed temporarily on the backend. Avoid uploading confidential documents until the hosting and retention setup has been fully verified.</p>
      </main>
    </div>
  )
}
