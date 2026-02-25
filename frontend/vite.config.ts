import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      // Proxy both API versions to the backend server.
      // This also enables SSE (EventSource) to work via relative URLs like
      // /api/v2/workflows/{id}/stream without CORS issues.
      '/api/v1': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/api/v2': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
