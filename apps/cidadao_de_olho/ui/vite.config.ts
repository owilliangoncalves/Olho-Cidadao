import path from "node:path";

import react from "@vitejs/plugin-react-swc";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, __dirname, "");
  const devApiProxyTarget =
    env.VITE_CITIZEN_DEV_API_PROXY_TARGET ?? "http://127.0.0.1:5150";

  return {
    plugins: [react(), tailwindcss()],
    base: "/static/ui/",
    server: {
      proxy: {
        // No dev isolado, o frontend continua chamando /api e o Vite repassa
        // para a aplicação Loco.rs local.
        "/api": {
          target: devApiProxyTarget,
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: path.resolve(__dirname, "../assets/static/ui"),
      emptyOutDir: true,
      sourcemap: false,
    },
  };
});
