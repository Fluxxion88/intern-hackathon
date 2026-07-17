import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // deploy/Dockerfile.web copies .next/standalone
  async rewrites() {
    // in docker the api is reachable by service name, in dev by localhost
    const api = process.env.API_ORIGIN || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${api}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
