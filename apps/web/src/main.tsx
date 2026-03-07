import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom';

function Nav() {
  return (
    <nav>
      <Link to="/">Live Console</Link> | <Link to="/overlay">Overlay</Link>
    </nav>
  );
}

function LiveView() {
  return (
    <main>
      <h1>Forza Telemetry Console</h1>
      <p>Live dashboard route scaffold.</p>
    </main>
  );
}

function OverlayView() {
  return (
    <main>
      <h1>Forza Overlay</h1>
      <p>OBS-friendly overlay route scaffold.</p>
    </main>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        <Route path="/" element={<LiveView />} />
        <Route path="/overlay" element={<OverlayView />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
