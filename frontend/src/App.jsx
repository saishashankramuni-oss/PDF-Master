import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Menu, X, Search, Sun, Moon, Globe, Shield, Lock, Image, FileText, Upload, Calendar, HelpCircle, Info, Trash, Loader2 } from 'lucide-react'

import {
  Navbar,
  Footer,
  ToolCard,
  UploadZone,
  FilePreview,
  FileList,
  ProcessingProgress,
  DownloadPanel,
  ErrorMessage,
  ConfirmationDialog,
  MobileNavigation,
} from './components'

const API_BASE = '/api'

export default function App() {
  const [userMode, setUserMode] = useState('guest')
  const [activeTool, setActiveTool] = useState<'merge' | 'split' | 'rotate' | 'compress' | 'protect' | 'unlock' | 'ocr' | 'organize' | null>(null)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [filePreview, setFilePreview] = useState<File | null>(null)
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const [showDownload, setShowDownload] = useState(false)
  const [downloadUrl, setDownloadUrl] = useState(null)
  const [showFilePreview, setShowFilePreview] = useState(false)
  const [showToolPage, setShowToolPage] = useState(false)
  const [theme, setTheme] = useState('light')

  // Check for PWA installation support
  useEffect(() => {
    const handleInstallPrompt = (e) => {
      e.preventDefault()
      setShowDownload(true)
    }

    window.addEventListener('beforeinstallprompt', handleInstallPrompt)

    return () => {
      window.removeEventListener('beforeinstallprompt', handleInstallPrompt)
    }
  }, [])

  // Handle theme toggle
  const handleThemeToggle = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
    document.documentElement.setAttribute('data-theme', theme === 'dark' ? 'dark' : 'light')
  }

  // Handle file upload
  const handleFileUpload = async (file: File) => {
    setUploadedFile(file)
    setError(null)
    setShowFilePreview(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const data = await response.json()
      setShowFilePreview(false)
      setShowDownload(true)
      setDownloadUrl(`/api/jobs/${data.job_id}/download?token=${data.download_token}`)
    } catch (err) {
      setShowFilePreview(false)
      setError(err.message)
    }
  }

  // Handle download
  const handleDownload = () => {
    if (downloadUrl) {
      window.location.href = downloadUrl
    }
  }

  // Reset state
  const resetState = () => {
    setUploadedFile(null)
    setFilePreview(null)
    setProcessing(false)
    setProgress(0)
    setError(null)
    setShowDownload(false)
    setDownloadUrl(null)
    setShowFilePreview(false)
  }

  // Handle file preview toggle
  const handlePreviewToggle = (file: File) => {
    setFilePreview(file)
    setShowFilePreview(true)
  }

  return (
      <div className="min-h-screen" data-theme={theme}>
        {/* Mobile Navigation */}
        <MobileNavigation theme={theme} onThemeToggle={handleThemeToggle} />

        {/* Main Content */}
        <div className="flex flex-col lg:flex-row min-h-screen">

          {/* Sidebar for desktop */}
          <nav className="lg:w-64 bg-white dark:bg-gray-900 flex flex-col h-screen border-r border-gray-200 dark:border-gray-700 shadow-lg">
            <Link to="/" className="py-4 px-6 font-bold text-xl text-primary-600 hover:text-primary-700">
              PDF Master
            </Link>
            <ul className="flex-1 py-6 space-y-2 px-4">
              <li>
                <Link to="/" className="flex items-center gap-3 text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-500 transition-colors">
                  <Grid className="w-6 h-6" />
                  <span>Tools</span>
                </Link>
              </li>
              <li>
                <Link to="/upload" className="flex items-center gap-3 text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-500 transition-colors">
                  <Upload className="w-6 h-6" />
                  <span>Upload</span>
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="flex items-center gap-3 text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-500 transition-colors">
                  <Shield className="w-6 h-6" />
                  <span>Privacy</span>
                </Link>
              </li>
            </ul>
          </nav>

          {/* Main Area */}
          <main className="flex-1 p-6 lg:p-8 overflow-x-hidden">
            {showToolPage && activeTool ? (
              <ToolPage
                tool={activeTool}
                onUpload={handleFileUpload}
                onPreviewToggle={handlePreviewToggle}
                theme={theme}
                onThemeToggle={handleThemeToggle}
              />
            ) : (
              <Homepage theme={theme} onThemeToggle={handleThemeToggle} />
            )}
          </main>
        </div>

        {/* Footer */}
        <Footer theme={theme} />

        {/* Error Message */}
        {error && <ErrorMessage message={error} />}

        {/* Download Panel */}
        {showDownload && downloadUrl && (
          <DownloadPanel
            url={downloadUrl}
            onClose={() => setShowDownload(false)}
            onDownload={handleDownload}
          />
        )}

        {/* File Preview */}
        {showFilePreview && filePreview && (
          <FilePreview
            file={filePreview}
            onClose={() => setShowFilePreview(false)}
          />
        )}

        {/* Confirmation Dialog */}
        <ConfirmationDialog
          isOpen={false}
          onConfirm={() => {}}
          onCancel={() => {}}
        />
      </div>
  )
}

// Homepage Component
function Homepage({ theme, onThemeToggle }) {
  const [isDark, setIsDark] = useState(false)

  const tools = [
    { id: 'merge', name: 'Merge PDF', category: 'Organize', icon: <ArrowRightAToB className="w-5 h-5" /> },
    { id: 'split', name: 'Split PDF', category: 'Organize', icon: <Search className="w-5 h-5" /> },
    { id: 'rotate', name: 'Rotate PDF', category: 'Organize', icon: <RotateCcw className="w-5 h-5" /> },
    { id: 'compress', name: 'Compress PDF', category: 'Optimize', icon: <Zap className="w-5 h-5" /> },
    { id: 'protect', name: 'Protect PDF', category: 'Security', icon: <LockClosed className="w-5 h-5" /> },
    { id: 'unlock', name: 'Unlock PDF', category: 'Security', icon: <Lock className="w-5 h-5" /> },
    { id: 'ocr', name: 'OCR PDF', category: 'Advanced', icon: <Scan className="w-5 h-5" /> },
    { id: 'organize', name: 'Organize Pages', category: 'Organize', icon: <Folder className="w-5 h-5" /> },
    { id: 'repair', name: 'Repair PDF', category: 'Optimize', icon: <Shield className="w-5 h-5" /> },
    { id: 'to-word', name: 'PDF to Word', category: 'Convert', icon: <FileText className="w-5 h-5" /> },
    { id: 'to-jpg', name: 'PDF to JPG', category: 'Convert', icon: <FileImage className="w-5 h-5" /> },
    { id: 'jpg-to-pdf', name: 'JPG to PDF', category: 'Convert', icon: <FileImage className="w-5 h-5" /> },
    { id: 'to-excel', name: 'PDF to Excel', category: 'Convert', icon: <FileSpreadsheet className="w-5 h-5" /> },
    { id: 'excel-to-pdf', name: 'Excel to PDF', category: 'Convert', icon: <FileSpreadsheet className="w-5 h-5" /> },
    { id: 'to-powerpoint', name: 'PDF to PowerPoint', category: 'Convert', icon: <FileType className="w-5 h-5" /> },
    { id: 'powerpoint-to-pdf', name: 'PowerPoint to PDF', category: 'Convert', icon: <FileType className="w-5 h-5" /> },
    { id: 'add-text', name: 'Add Text', category: 'Edit', icon: <Type className="w-5 h-5" /> },
    { id: 'add-image', name: 'Add Image', category: 'Edit', icon: <Image className="w-5 h-5" /> },
    { id: 'add-watermark', name: 'Add Watermark', category: 'Edit', icon: <Stamp className="w-5 h-5" /> },
    { id: 'add-page-numbers', name: 'Add Page Numbers', category: 'Edit', icon: <Hash className="w-5 h-5" /> },
    { id: 'add-signature', name: 'Add Signature', category: 'Edit', icon: <PenTool className="w-5 h-5" /> },
    { id: 'add-annotation', name: 'Add Annotation', category: 'Edit', icon: <Highlighter className="w-5 h-5" /> },
    { id: 'redact', name: 'Redact PDF', category: 'Advanced', icon: <Eye className="w-5 h-5" /> },
    { id: 'compare', name: 'Compare PDF', category: 'Advanced', icon: <FileSearch className="w-5 h-5" /> },
    { id: 'extract-text', name: 'Extract Text', category: 'Advanced', icon: <FileText className="w-5 h-5" /> },
    { id: 'extract-images', name: 'Extract Images', category: 'Advanced', icon: <FileImage className="w-5 h-5" /> },
    { id: 'metadata', name: 'PDF Metadata', category: 'Advanced', icon: <FileJson className="w-5 h-5" /> },
    { id: 'preview', name: 'Page Preview', category: 'Advanced', icon: <Layout className="w-5 h-5" /> },
  ]

  return (
    <section className={`flex-1 pt-8 ${isDark ? 'bg-gray-900' : 'bg-white'}`}>
      <header className="mb-8">
        <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-4">
          Everything You Need to Work with PDFs
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl">
          Professional PDF processing made simple. No installation required.
        </p>
      </header>

      {/* Popular Tools Section */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Popular Tools</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {tools.map((tool) => (
            <ToolCard
              key={tool.id}
              tool={tool}
              onSelect={() => {
                setActiveTool(tool.id as any)
                setShowToolPage(true)
              }}
            />
          ))}
        </div>
      </div>

      {/* PDF Tool Categories */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">PDF Tool Categories</h2>
        <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
          <span className="px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs text-gray-600 dark:text-gray-300">
            Organize
          </span>
          <span className="px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs text-gray-600 dark:text-gray-300">
            Optimize
          </span>
          <span className="px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs text-gray-600 dark:text-gray-300">
            Convert
          </span>
          <span className="px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs text-gray-600 dark:text-gray-300">
            Edit
          </span>
          <span className="px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs text-gray-600 dark:text-gray-300">
            Security
          </span>
          <span className="px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs text-gray-600 dark:text-gray-300">
            Advanced
          </span>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="mt-8 p-6 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-medium text-gray-900 dark:text-gray-100 mb-4">How It Works</h2>
        <ol className="list-decimal list-inside space-y-2 text-sm text-gray-600 dark:text-gray-400">
          <li>Select a PDF tool</li>
          <li>Upload your document</li>
          <li>Processing starts automatically</li>
          <li>Download your result</li>
          <li>Files are automatically deleted</li>
        </ol>
      </div>

      {/* Privacy Section */}
      <div className="mt-8 p-6 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-medium text-gray-900 dark:text-gray-100 mb-4">Privacy & Security</h2>
        <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400">
          <li>Files processed in temporary directories</li>
          <li>Automatic deletion within 30 minutes</li>
          <li>No permanent storage of documents</li>
          <li>Secure processing with HTTPS</li>
        </ul>
      </div>
    </section>
  )
}

// Tool Page Component
function ToolPage({ tool, onUpload, onPreviewToggle, theme, onThemeToggle }) {
  const [file, setFile] = useState<File | null>(null)
  const [progressValue, setProgressValue] = useState(0)
  const [isProcessing, setIsProcessing] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  // Map tool IDs to API endpoints
  const operationMap: Record<string, string> = {
    merge: 'merge',
    split: 'split',
    rotate: 'rotate',
    compress: 'compress',
    protect: 'protect',
    unlock: 'unlock',
    ocr: 'ocr',
    organize: 'organize',
    repair: 'repair',
    'to-word': 'to-word',
    'to-jpg': 'to-jpg',
    'jpg-to-pdf': 'jpg-to-pdf',
    'to-excel': 'to-excel',
    'excel-to-pdf': 'excel-to-pdf',
    'to-powerpoint': 'to-powerpoint',
    'powerpoint-to-pdf': 'powerpoint-to-pdf',
    'add-text': 'add-text',
    'add-image': 'add-image',
    'add-watermark': 'add-watermark',
    'add-page-numbers': 'add-page-numbers',
    'add-signature': 'add-signature',
    'add-annotation': 'add-annotation',
    'redact': 'redact',
    'compare': 'compare',
    'extract-text': 'extract-text',
    'extract-images': 'extract-images',
    'metadata': 'metadata',
    'preview': 'preview',
  }

  const processPDF = async () => {
    if (!file) return

    setIsProcessing(true)
    setProgressValue(0)
    setErrorMsg('')

    try {
      const formData = new FormData()
      formData.append('file', file)

      const operation = operationMap[tool]
      if (!operation) {
        throw new Error('Unknown tool operation')
      }

      const response = await fetch(`${API_BASE}/${operation}`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Processing failed')
      }

      const data = await response.json()
      setProgressValue(100)
      setIsProcessing(false)
      setShowDownload(true)
      setDownloadUrl(`/api/jobs/${data.job_id}/download?token=${data.download_token}`)

    } catch (error) {
      setErrorMsg(error.message)
      setIsProcessing(false)
    }
  }

  return (
    <section className="pt-8">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
          {tool.name}
        </h2>

        {/* Upload Area with preview */}
        <UploadZone
          onFileSelected={setFile}
          acceptedFiles=".pdf"
          onProcess={processPDF}
          showPreview={true}
        />

        {/* Show file preview if uploaded */}
        {file && (
          <FilePreview
            file={file}
            onClose={() => setShowFilePreview(false)}
          />
        )}

        {/* Processing State */}
        {isProcessing && (
          <ProcessingProgress
            progress={progressValue}
            message="Processing your PDF..."
          />
        )}

        {/* Error Message */}
        {errorMsg && <ErrorMessage message={errorMsg} />}

        {/* Success/Download State */}
        {!isProcessing && file && (
          <div className="mt-6 p-4 bg-green-50 dark:bg-green-900 rounded-lg border border-green-200 dark:border-green-800">
            <h3 className="font-medium text-green-800 dark:text-green-300">
              PDF processed successfully!
            </h3>
            <DownloadPanel
              url={downloadUrl}
              onClose={() => setShowDownload(false)}
              onDownload={handleDownload}
            />
          </div>
        )}
      </div>
    </section>
  )
}