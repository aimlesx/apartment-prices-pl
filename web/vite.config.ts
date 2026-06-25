import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Backend FastAPI wskazywany przez API_TARGET (domyślnie :8000, tak jak `make serve`).
// Aplikacja odwołuje się do API ścieżkami względnymi (/predict, /health), a Vite
// przekierowuje te żądania do backendu — dzięki temu nie ma CORS-a i nie trzeba
// zmieniać serwisu.
// Inny port (np. gdy 8000 jest zajęty):  API_TARGET=http://localhost:8200 npm run dev
const API_TARGET = process.env.API_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/predict": API_TARGET,
      "/health": API_TARGET,
    },
  },
});
