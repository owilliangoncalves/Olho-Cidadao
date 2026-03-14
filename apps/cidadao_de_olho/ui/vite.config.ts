import path from "node:path";

import react from "@vitejs/plugin-react-swc";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "/static/ui/",
  build: {
    outDir: path.resolve(__dirname, "../assets/static/ui"),
    emptyOutDir: true,
    sourcemap: false,
    rollupOptions: {
      output: {
        entryFileNames: "assets/[name].js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: (assetInfo) => {
          const name = assetInfo.names?.[0] ?? assetInfo.name ?? "asset";
          if (name.endsWith(".css")) {
            return "assets/[name].css";
          }
          return "assets/[name][extname]";
        },
      },
    },
  },
});
