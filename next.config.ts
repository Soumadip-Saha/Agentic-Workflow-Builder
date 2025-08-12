// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // We remove 'output: "export"' because it is incompatible with the server-side proxy.
  async rewrites() {
    return [
      {
        source: "/api/invoke", // The path the frontend calls
        destination: "http://127.0.0.1:8000/api/invoke", // Where the request is sent
      },
    ];
  },
};

export default nextConfig;