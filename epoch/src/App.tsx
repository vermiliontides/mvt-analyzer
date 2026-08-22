import React from 'react';

export default function App() {
  return (
    <div style={{ fontFamily: 'sans-serif', padding: '2rem', color: '#111', background: '#f9f9f9', height: '100vh', boxSizing: 'border-box' }}>
      <header style={{ borderBottom: '1px solid #ddd', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 600 }}>Verichron Epoch</h1>
        <p style={{ margin: '0.5rem 0 0', color: '#666', fontSize: '0.9rem' }}>Cross-Platform Forensic Desktop Environment</p>
      </header>
      <main style={{ background: '#fff', padding: '1.5rem', borderRadius: '8px', border: '1px solid #e1e4e8' }}>
        <h2 style={{ fontSize: '1.2rem', marginTop: 0 }}>Frontend Presentation Layer Active</h2>
        <p style={{ color: '#444' }}>The Electron renderer and React workspace are successfully communicating.</p>
      </main>
    </div>
  );
}