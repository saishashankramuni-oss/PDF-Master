import React from 'react'
import { X, Menu, Search } from 'lucide-react'

export default function MobileNavigation() {
  const [isMenuOpen, setIsMenuOpen] = React.useState(false)
  const [isSearchOpen, setIsSearchOpen] = React.useState(false)

  return (
    <nav className="hidden lg:hidden md:block bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <button
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className={`p-2 rounded-lg transition-colors ${isMenuOpen ? 'bg-primary-100' : 'hover:bg-gray-100'} ${isMenuOpen ? 'text-primary-600' : 'text-gray-600'}`}
          aria-label="Open menu"
        >
          {isMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        <div className="hidden md:hidden lg:flex items-center gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
            <input
              type="text"
              placeholder="Search..."
              className="pl-8 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        {/* Mobile menu */}
        {isMenuOpen && (
          <div className="mt-6 space-y-4">
            <Link to="/" className="text-lg text-gray-800 dark:text-gray-200 hover:text-primary-600 transition-colors">
              Home
            </Link>
            <Link to="/upload" className="text-lg text-gray-800 dark:text-gray-200 hover:text-primary-600 transition-colors">
              Upload
            </Link>
            <Link to="/privacy" className="text-lg text-gray-800 dark:text-gray-200 hover:text-primary-600 transition-colors">
              Privacy
            </Link>
          </div>
        )}
      </div>
    </nav>
  )
}