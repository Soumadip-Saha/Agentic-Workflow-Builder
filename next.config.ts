// next.config.js

/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        // CHANGE #1: Make the source "greedy" to capture all API calls.
        source: "/api/:path*",

        // CHANGE #2: Make the destination dynamic and use the same path.
        destination:
          process.env.NODE_ENV === "development"
            ? // In LOCAL, forward to the Python server, preserving the path.
              "http://127.0.0.1:8000/api/:path*"
            : // In PRODUCTION, forward to the Vercel function, preserving the path.
              "/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;