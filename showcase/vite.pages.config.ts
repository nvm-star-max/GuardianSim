import react from "@vitejs/plugin-react";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

const showcaseRoot = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  base: "/GuardianSim/",
  root: resolve(showcaseRoot, "static-site"),
  publicDir: resolve(showcaseRoot, "public"),
  plugins: [react()],
  css: {
    postcss: resolve(showcaseRoot, "postcss.config.mjs"),
  },
  build: {
    emptyOutDir: true,
    outDir: resolve(showcaseRoot, "pages-dist"),
  },
});
