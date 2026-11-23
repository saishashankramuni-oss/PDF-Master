import React from 'react'
import { Menu, X, Search, Sun, Moon } from 'lucide-react'

export default function Navbar({
  isOpen = false,
  onToggle,
  onSearch,
  theme = 'light',
  onThemeToggle
}) {
  return (
    <nav className="bg-white dark:bg-gray-900 shadow-lg sticky top-0 z-50 border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Left side - Logo and Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-600 flex items-center justify-center">
            <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">PDF Master</span>
        </div>

        {/* Right side - Navigation and Actions */}
        <div className="flex items-center gap-4">
          {/* Theme Toggle */}
          <button
            onClick={onThemeToggle}
            className={`rounded-lg transition-colors ${theme === 'dark' ? 'bg-primary-100 dark:bg-primary-900' : 'bg-gray-100 dark:bg-gray-900'}`}
            aria-label="Toggle theme"
          >
            {theme === 'light' ? (
              <Moon className="w-5 h-5" />
            ) : (
              <Sun className="w-5 h-5" />
            )}
          </button>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
            <input
              type="text"
              placeholder="Search..."
              className="pl-8 pr-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              onBlur={() => onSearch && onSearch()}
            />
          </div>

          {/* Menu Button (mobile) */}
          {/** @jsxImportSource react **/
            <button
              onClick={onToggle}
              className={`p-2 rounded-lg transition-colors ${isOpen ? 'bg-primary-100' : 'hover:bg-gray-100'} ${isOpen ? 'text-primary-600' : 'text-gray-600'}`}
              aria-label="Open menu"
            >
              {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          {/* */}
        </div>
      </div>
    </nav>
  )
}