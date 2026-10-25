import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev, proxy /api to the FastAPI server so the same relative URLs work everywhere.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": process.env.API_PROXY || "http://localhost:8000" } },
});
