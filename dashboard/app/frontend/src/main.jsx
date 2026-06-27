import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { UnitSystemProvider } from './context/UnitSystemContext.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <UnitSystemProvider>
      <App />
    </UnitSystemProvider>
  </React.StrictMode>,
)
