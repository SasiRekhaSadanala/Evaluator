from backend.app.main import app

print("Registered routes:")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        print(f"  {route.methods} {route.path}")

print("\nEvaluate endpoint ready at: POST /api/evaluate")
