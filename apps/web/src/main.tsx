import React from 'react';
import ReactDOM from 'react-dom/client';

function App() {
  return <main><h1>Forza web</h1></main>;
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
