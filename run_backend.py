import sys
import traceback
import os

# Ensure we are in the right directory
current_dir = os.getcwd()
sys.path.append(current_dir)

print(f"Starting backend from {current_dir}...")

try:
    # Check Imports
    import pydantic
    print(f"Pydantic version: {pydantic.VERSION}")
    
    import uvicorn
    from backend.app.main import app
    
    # Run Server
    print("Launching Uvicorn on 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
except BaseException:
    print("CRITICAL FAILURE")
    with open("startup_error.log", "w") as f:
        f.write(traceback.format_exc())
        f.write("\n\n")
        try:
            import pydantic
            f.write(f"Pydantic Version: {pydantic.VERSION}\n")
        except:
            f.write("Pydantic not found\n")
