import { defineConfig } from "vite";

export default defineConfig({
  resolve: {
    alias: [
      { find: /^three$/, replacement: "three/webgpu" },
    ],
  },
  build: {
    chunkSizeWarningLimit: 3200,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules/three")) return "rendering";
          if (id.includes("node_modules/@dimforge/rapier3d")) return "physics-wasm";
          return undefined;
        },
      },
    },
  },
});
