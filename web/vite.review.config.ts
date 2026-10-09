import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";

export default defineConfig({
  base: "./",
  plugins: [react()],
  build: {
    outDir: "dist-review",
    emptyOutDir: true,
    cssCodeSplit: false,
    rollupOptions: { input: fileURLToPath(new URL("./v2-review.html", import.meta.url)) },
  },
});
