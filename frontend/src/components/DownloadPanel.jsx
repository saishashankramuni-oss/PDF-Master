import React from 'react'
import { Download } from 'lucide-react'

export interface DownloadPanelProps {
  url: string
  onClose: () => void
  onDownload: () => void
}

export default function DownloadPanel({ url, onClose, onDownload }) {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-zxl z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-900 rounded-lg p-8 max-w-md w-full border border-gray-200 dark:border-gray-700 shadow-2xl">
        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
          Ready for Download
        </h3>

        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Your PDF is ready. Click below to download.
        </p>

        <div className="flex gap-3">
          <button
            onClick={onDownload}
            className={`flex-1 py-3 px-4 rounded-lg font-medium bg-primary-600 text-white hover:bg-primary-700 transition-colors`}
          >
            <Download className="mr-2 w-4 h-4" />
            Download
          </button>
          <button
            onClick={onClose}
            className={`flex-1 py-3 px-4 rounded-lg font-medium border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors`}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}