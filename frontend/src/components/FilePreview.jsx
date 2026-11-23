import React from 'react'
import { FileText, Image, Loader2, X } from 'lucide-react'

export interface FilePreviewProps {
  file: File | null
  showFullDetails?: boolean
  onClose: () => void
}

export default function FilePreview({
  file,
  showFullDetails = false,
  onClose
}: FilePreviewProps) {
  if (!file) return null

  const [isLoading, setIsLoading] = React.useState(true)
  const [pageCount, setPageCount] = React.useState(0)
  const [fileSizeMB, setFileSizeMB] = React.useState(0)

  // Calculate file size
  React.useEffect(() => {
    if (file) {
      setFileSizeMB((file.size / (1024 * 1024)).toFixed(2))
    }
  }, [file])

  // Try to get PDF info using pdf.js if available
  React.useEffect(() => {
    if (!file) return

    const loadPdf = async () => {
      try {
        // Use pdf.js via CDN
        if (typeof pdfjsLib !== 'undefined') {
          const url = URL.createObjectURL(file)
          const loadingTask = pdfjsLib.getDocument({ url })

          loadingTask.promise.then(async (pdf) => {
            const numPages = pdf.numPages
            setPageCount(numPages)
            setIsLoading(false)

            // Try to get text from first page
            try {
              const page = await pdf.getPage(1)
              const textContent = await page.getTextContent()
              const text = textContent.items.map((item: any) => item.str).join(' ')
              // We'll just show page count, not full text preview
            } catch (e) {
              // Ignore errors getting text
            }
          }).catch((error) => {
            console.error('PDF.js error:', error)
            setIsLoading(false)
          })
        } else {
          // pdf.js not loaded, just show basic info
          setIsLoading(false)
        }
      } catch (error) {
        console.error('Failed to load PDF preview:', error)
        setIsLoading(false)
      }
    }

    loadPdf()
  }, [file])

  return (
    <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 max-w-md mx-auto">
      <div className="flex items-start gap-3">
        {/* Loading state */}
        {isLoading && (
          <div className="flex-1">
            <Loader2 className="w-5 h-5 text-primary-500 mt-1" />
            <span className="text-sm text-gray-500 dark:text-gray-400">Loading PDF...</span>
          </div>
        )}

        {/* Preview content */}
        {!isLoading && (
          <div className="flex-1 min-h-24">
            {/* File info */}
            <div className="pb-2 border-b border-gray-200 dark:border-gray-700">
              <h4 className="font-medium text-gray-900 dark:text-gray-100">
                {file.name}
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {pageCount} page{s(pageCount)} • {fileSizeMB} MB
              </p>
            </div>

            {/* Page count indicator */}
            {pageCount > 0 && (
              <p className="text-xs text-gray-400 dark:text-gray-500">
                Pages: {pageCount}
              </p>
            )}

            {/* Close button */}
            <button
              onClick={onClose}
              className="ml-auto text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-400"
              aria-label="Close preview"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function s(count: number): string {
  return count !== 1 ? 'pages' : 'page'
}