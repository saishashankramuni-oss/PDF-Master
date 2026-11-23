import React from 'react'
import { Mail, Phone, Globe } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-gray-900 dark:bg-gray-100 text-gray-400 dark:text-gray-600 py-8 border-t border-gray-800 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* About */}
          <div>
            <h4 className="font-medium text-white mb-4">PDF Master</h4>
            <p className="text-sm">
              Professional PDF processing made simple. No installation required. All files processed temporarily and securely.
            </p>
          </div>

          {/* Tools */}
          <div>
            <h4 className="font-medium text-white mb-4">Tools</h4>
            <ul className="space-y-2">
              <li className="text-sm">
                <a href="#merge" className="hover:text-primary-400 transition-colors">Merge PDF</a>
              </li>
              <li className="text-sm">
                <a href="#split" className="hover:text-primary-400 transition-colors">Split PDF</a>
              </li>
              <li className="text-sm">
                <a href="#compress" className="hover:text-primary-400 transition-colors">Compress PDF</a>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="font-medium text-white mb-4">Legal</h4>
            <ul className="space-y-2">
              <li className="text-sm">
                <a href="#privacy" className="hover:text-primary-400 transition-colors">Privacy Policy</a>
              </li>
              <li className="text-sm">
                <a href="#terms" className="hover:text-primary-400 transition-colors">Terms of Service</a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-6 pt-6 border-t border-gray-800 dark:border-gray-700 text-center">
          <p className="text-sm">
            © {new Date().getFullYear()} PDF Master. All rights reserved.
          </p>
          <p className="text-xs mt-1">
            Automatic file deletion within 30 minutes. No permanent storage.
          </p>
        </div>
      </div>
    </footer>
  )
}