import React from 'react'
import ReactDOM from 'react-dom/client'
import { Provider } from 'react-dom'
import App from './App'
import './index.css'

// Initialize the app
const root = ReactDOM.createRoot(document.getElementById('root'))
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)