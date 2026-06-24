# run_backend.py
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Render sets $PORT, local defaults to 8000

    print(f"Starting Evaluator 2.0 backend on port {port}...")

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",   # must be 0.0.0.0 for Render — never 127.0.0.1
        port=port,
        reload=False,      # never True in production
        workers=1          # free tier only supports 1 worker
    )
