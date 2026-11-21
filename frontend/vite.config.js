import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// All data comes from ../server.py (python3 server.py, port 8100).
export default defineConfig({
  base: process.env.VITE_BASE || '/',
  plugins: [react()],
  server: { port: 5174, proxy: { '/api': 'http://127.0.0.1:8100' } },
});
