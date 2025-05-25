import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',   // <— добавьте эту строку
    port: 3000
  },
  resolve: {
    alias: { '@': '/src' }
  }
});
