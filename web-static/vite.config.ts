import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Relative base so the static build works from any Bono Host docroot or subfolder.
export default defineConfig({
  base: "./",
  plugins: [react()],
  build: {
    outDir: "dist",
    target: "es2020",
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Keep the heavy WebGL stack in its own lazy chunk.
          if (id.includes("three") || id.includes("@react-three")) {
            return "webgl";
          }
        },
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
  },
});
