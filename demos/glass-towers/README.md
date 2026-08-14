# Glass Towers

A standalone Three.js WebGPU and Rapier WASM browser game about balancing translucent pieces on a small pedestal.

The renderer selects WebGPU when the browser and GPU support it, then falls back to WebGL 2 through the same Three.js `WebGPURenderer` pipeline. Rapier provides the fixed-step rigid-body simulation from an embedded WebAssembly module. Add `?renderer=webgl2` to the URL to exercise the fallback explicitly.

```powershell
npm install
npm run dev
```

Controls: move the pointer or use `A`/`D` and arrow keys, then click, tap, `Space`, or `Enter` to drop. Press `R` or use the restart control to begin again.

Quality checks:

```powershell
npm run lint
npm test
npm run build
npm run test:browser
```

Browser evidence is written to `artifacts/` and is intentionally ignored by Git.
