import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/postcss';
import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';
export default defineConfig({
  plugins: [react()],
  // Pass only Vercel's public client configuration into the browser bundle.
  define: {
    'import.meta.env.VITE_SPEED_INSIGHTS_CONFIG': JSON.stringify(process.env.VERCEL_OBSERVABILITY_CLIENT_CONFIG ?? process.env.VITE_VERCEL_OBSERVABILITY_CLIENT_CONFIG ?? ''),
  },
  resolve: { alias: { '@': fileURLToPath(new URL('.', import.meta.url)) } },
  css: { postcss: { plugins: [tailwindcss()] } },
  server: { host: '127.0.0.1', port: 5190, strictPort: true, proxy: { '/physics': { target: 'http://127.0.0.1:5192', rewrite: path => path.replace(/^\/physics/, '') } } },
});
