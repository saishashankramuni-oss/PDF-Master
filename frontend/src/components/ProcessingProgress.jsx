import React from 'react'
import { Loader2 } from 'lucide-react'

export interface ProcessingProgressProps {
  progress: number
  message: string
}

export default function ProcessingProgress({ progress, message }) {
  const percentage = Math.max(0, Math.min(100, progress))

  return (
    <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="flex items-start gap-3">
        <Loader2 className="w-5 h-5 text-primary-500 mt-1" />
        <div>
          <p className="font-medium text-gray-900 dark:text-gray-100">
            {message}
          </p>
          <div className="mt-2">
            <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2 w-full">
              <div
                className="bg-primary-600 rounded-full h-2 transition-width ease-out duration-300"
                style={{ width: `${percentage}%` }}
              />
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-400 ml-auto">
              {percentage}%
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}