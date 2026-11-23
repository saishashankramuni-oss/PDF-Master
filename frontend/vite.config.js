import {defineConfig} from 'vite'
import react from '@vitejs/plugin-react'
import viteTsconfigPaths from 'vite-tsconfig-paths'
import {VitePWAPlugin} from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    viteTsconfigPaths(),
    VitePWAPlugin({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'PDF Master',
        short_name: 'PDF Master',
        description: 'Everything You Need to Work with PDFs',
        theme_color: '#ffffff',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
      },
    }),
  ],
  server: {
    port: 3000,
  },
  // Inject the service worker registration code into the app
  // This will be included in the generated index.html
})