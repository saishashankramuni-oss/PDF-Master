import React from 'react'
import { AlertCircle } from 'lucide-react'

export interface ErrorMessageProps {
  message: string
  isError?: boolean
}

export default function ErrorMessage({ message, isError = true }) {
  const bgColor = isError ? 'bg-red-100' : 'bg-green-100'
  const textColor = isError ? 'text-red-800' : 'text-green-800'
  const iconColor = isError ? 'text-red-500' : 'text-green-500'

  return (
    <div className={`p-4 rounded-lg ${bgColor} border ${borderColor ? borderColor : 'border-red-200 dark:border-green-200'} mb-4`}
      role="alert"
    >
      <AlertCircle className={`w-5 h-5 ${iconColor} mr-3 inline-block` } />
      <span className={`text-sm ${textColor}`}>{message}</span>
    </div>
  )
}