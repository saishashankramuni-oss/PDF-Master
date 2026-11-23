import React from 'react'
import { ArrowRightAToB, Search, ArrowRight, Zap, LockClosed, Lock, Image, Folder, RotateCcw, Shield, FileText, FileImage, FileSpreadsheet, FileType, FileVideo, Type, Edit2, Stamp, Hash, PenTool, Highlighter, Scan, Eye, FileSearch, Scissors, FileJson, Layout } from 'lucide-react'

export interface ToolCardProps {
  tool: {
    id: string
    name: string
    category: string
    icon: React.ComponentType<{ className?: string }>
  }
  onSelect: () => void
}

export default function ToolCard({ tool, onSelect }) {
  return (
    <div
      onClick={onSelect}
      className="group cursor-pointer rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-500 transition-colors transform hover:scale-105"
    >
      <div className="p-4 rounded-t-lg">
        <tool.icon className="w-6 h-6 text-primary-600" />
      </div>
      <div className="p-4">
        <h3 className="font-medium text-gray-900 dark:text-gray-100 line-clamp-1">{tool.name}</h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-1">{tool.category}</p>
      </div>
    </div>
  )
}