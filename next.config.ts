import type { NextConfig } from "next";

// Turbopack auto-detects the project root from package.json.
// Hardcoding it breaks builds on any machine that is not the original dev box.
// `output: "standalone"` makes the production bundle self-contained so
// Dockerfile + `node server.js` is all that's needed at runtime.
const nextConfig: NextConfig = {
  output: "standalone",
};

export default nextConfig;
