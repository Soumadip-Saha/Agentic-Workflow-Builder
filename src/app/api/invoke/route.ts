// src/app/api/invoke/route.ts

// This tells Next.js to always run this function dynamically, disabling caching.
export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  try {
    // 1. Get the request body that the client sent.
    const body = await req.json();

    const pythonServerUrl = process.env.VERCEL_URL
    // In PRODUCTION, the endpoint is the full path based on the filename.
    ? `https://${process.env.VERCEL_URL}/api/python_handler`
    // In LOCAL, the endpoint is the root of the server running on port 8005.
    : 'http://127.0.0.1:8005/';
    const pythonResponse = await fetch(pythonServerUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    // 3. Check if the Python server responded correctly.
    if (!pythonResponse.ok) {
      const errorText = await pythonResponse.text();
      throw new Error(`Python server responded with ${pythonResponse.status}: ${errorText}`);
    }

    // 4. This is the critical part: Get the streaming body from the Python response.
    const stream = pythonResponse.body;

    // 5. Return a new streaming response to the original client,
    //    piping the stream from the Python server directly through.
    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error("Error in streaming proxy:", error);
    // Return a proper error response if the proxy fails
    return new Response(JSON.stringify({ error: 'Proxy error' }), { status: 500 });
  }
}