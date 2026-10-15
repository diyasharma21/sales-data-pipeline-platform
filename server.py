import argparse
import os
import uvicorn

if __name__ == "__main__":
    default_host = os.getenv("API_HOST", os.getenv("HOST", "127.0.0.1"))
    default_port = int(os.getenv("API_PORT", os.getenv("PORT", "8000")))

    parser = argparse.ArgumentParser(description="Sales Data Platform Backend Server")
    parser.add_argument("--host", default=default_host, help=f"Host interface (default: {default_host})")
    parser.add_argument("--port", type=int, default=default_port, help=f"Port (default: {default_port})")
    parser.add_argument("--reload", action="store_true", help="Enable live auto-reload")
    args = parser.parse_args()

    uvicorn.run("src.api.app:app", host=args.host, port=args.port, reload=args.reload)
