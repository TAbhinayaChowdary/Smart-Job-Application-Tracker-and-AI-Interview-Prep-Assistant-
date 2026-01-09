import sys
import os

# Add the current directory to sys.path so we can import backend
sys.path.append(os.getcwd())

try:
    from backend.app.main import app
    print("Successfully imported app.")
    print("Routes:")
    found = False
    for route in app.routes:
        print(f" - {route.path} {route.name}")
        if route.path == "/auth/login":
            found = True
    
    if found:
        print("\nSUCCESS: /auth/login route is registered!")
    else:
        print("\nFAILURE: /auth/login route is NOT found.")
        
except Exception as e:
    print(f"Error importing app: {e}")
    import traceback
    traceback.print_exc()
