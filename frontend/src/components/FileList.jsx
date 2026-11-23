import React from 'react'
import { FileText, Trash, Loader2, CheckCircle } from 'lucide-react'

export interface FileListProps {
  files: Array<{ name: string; size: number; type: string }>
  onRemove?: (index: number) => void
  disabled?: boolean
}

export default function FileList({ files, onRemove, disabled = false }) {
  return (
    <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
      <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-3">
        {files.length} file{s(files.length)}
      </h4>
      {files.length === 0 && (
        <p className="text-gray-500 dark:text-gray-400 italic">
          No files added
        </p>
      )}
      <ul className="space-y-2 max-h-40 overflow-y-auto">
        {files.map((file, index) => (
          <li key={index} className="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded">
            <FileText className="w-4 h-4 text-gray-400" />
            <span className="flex-1 font-medium text-gray-900 dark:text-gray-100">
              {file.name}
            </span>
            <button
              onClick={() => onRemove && onRemove(index)}
              disabled={disabled}
              className="text-red-500 hover:text-red-700 text-sm"
              aria-label="Remove file"
            >
              <Trash className="w-3 h-3" />
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

function s(count: number): string {
  return count !== 1 ? 's' : ''
}