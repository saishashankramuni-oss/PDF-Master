import React, { useState } from 'react'
import { Plus, DragHorizontal, CheckCircle, XCircle, Eye, Loader2 } from 'lucide-react'

export interface UploadZoneProps {
  acceptedFiles?: string
  onFileSelected: (file: File) => void
  onProcess?: () => void
  disabled?: boolean
  showPreview?: boolean
}

export default function UploadZone({
  acceptedFiles = '.pdf',
  onFileSelected,
  onProcess,
  disabled = false,
  showPreview = true
}):
  const [hasFile, setHasFile] = useState(false)
  const [fileName, setFileName] = useState('')
  const [fileSize, setFileSize] = useState(0)
  const [fileType, setFileType] = useState('')
  const [browsing, setBrowsing] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  // Validate PDF signature
  const validatePdfSignature = (file: File): boolean => {
    return new Promise((resolve) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const result = e.target?.result
        if (result && typeof result === 'string') {
          resolve(result.startsWith('%PDF-'))
        } else {
          resolve(false)
        }
      }
      reader.readAsDataURL(file)
    })
  }

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate file type
      if (acceptedFiles && !file.name.toLowerCase().endsWith('.pdf')) {
        alert('Please upload a PDF file')
        return
      }

      // Validate PDF signature
      const isValidPdf = await validatePdfSignature(file)
      if (!isValidPdf) {
        alert('Invalid PDF file. The file does not have valid PDF signatures.')
        return
      }

      setHasFile(true)
      setFileName(file.name)
      setFileSize(file.size)
      setFileType(file.type || 'application/pdf')
      onFileSelected(file)

      // Generate preview if supported
      if (showPreview) {
        const url = URL.createObjectURL(file)
        setPreviewUrl(url)
      }
    }
  }

  const browseClick = () => {
    setBrowsing(true)
  }

  // Clean up preview URL on unmount
  React.useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
      }
    }
  }, [previewUrl])

  return (
    <div
      className={`
        border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer p-8 text-center transition-all duration-300 flex flex-col items-center justify-center ${hasFile}
          ? "bg-primary-50 dark:bg-primary-900 border-primary-500"
          : "bg-gray-50 dark:bg-gray-800"
      `}
        onMouseEnter={browseClick}
        onMouseLeave={browseClick}
    >
      <div className="flex flex-col items-center gap-4 w-full">
        {/* Upload Icon */}
        <div className={`w-14 h-14 ${hasFile ? 'text-primary-600' : 'text-gray-400 dark:text-gray-500'} flex items-center justify-center`}
          onClick={browseClick}
        >
          {hasFile ? (
            <>
              <CheckCircle className="w-7 h-7" />
              <p className="text-xs mt-1 text-gray-600 dark:text-gray-400">PDF Selected</p>
            </>
          ) : (
            <DragHorizontal className="w-7 h-7" />
          )}
        </div>

        {/* Text */}
        <h3 className={`font-medium text-gray-900 dark:text-gray-100 text-center ${
          hasFile ? 'text-primary-600' : 'text-gray-500 dark:text-gray-400'
        }`}>
          {hasFile ? ` ${fileName}` : 'Drag and drop a PDF here'}
        </h3>

        {/* File details */}
        {hasFile && (
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">
            <div>
              <span className="font-medium">Size:</span> {formatFileSize(fileSize)}
            </div>
            <div>
              <span className="font-medium">Type:</span> {fileType}
            </div>
          </div>
        )}

        {/* Preview Button (for multi-page PDFs) */}
        {hasFile && !previewUrl && (
          <button
            onClick={browseClick}
            className="mt-2 w-full py-2 rounded-lg font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            type="button"
          >
            <Eye className="mr-2 w-4 h-4" /> Preview PDF
          </button>
        )}

        {/* File Input */}
        <input
          type="file"
          accept={acceptedFiles}
          className="hidden"
          onChange={handleChange}
        />

        {/* Browse Button */}
        <button
          onClick={browseClick}
          disabled={disabled}
          className={`w-full py-2.5 px-4 rounded-lg font-medium text-gray-800 dark:text-gray-200 ${
            disabled ? 'opacity-50 cursor-not-allowed' : 'bg-primary-600 text-white hover:bg-primary-700 transition-colors'
          }`}
          type="button"
        >
          Browse Files
        </button>
      </div>
    </div>
  )

function formatFileSize(bytes: number): string {
  if (bytes >= 1024 * 1024 * 1024) {
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
  }
  if (bytes >= 1024 * 1024) {
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }
  if (bytes >= 1024) {
    return (bytes / 1024).toFixed(2) + ' KB'
  }
  return bytes + ' bytes'
}