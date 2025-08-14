// next.config.js

/** @type {import('next').NextConfig} */
const nextConfig = {
  // We keep 'output: "export"' commented out or removed because it is
  // incompatible with server-side features like rewrites.
  async rewrites() {
    return [
      {
        // The 'source' path is the "virtual" endpoint that your
        // frontend will call. It doesn't need to correspond to a real file.
        source: "/api/invoke",

        // The 'destination' is now dynamic, changing based on the environment.
        destination:
          process.env.NODE_ENV === "development"
            ? // In LOCAL development, forward the request to your
              // running Uvicorn server at its root, since your
              // FastAPI route is defined as @app.post("/").
              "http://127.0.0.1:8000/"
            : // In PRODUCTION on Vercel, forward the request internally
              // to the serverless function. Vercel knows that /api/invoke
              // corresponds to the /api/invoke.py file. This is secure
              // and bypasses the Vercel Authentication layer.
              "/api/invoke",
      },
    ];
  },
};

module.exports = nextConfig;