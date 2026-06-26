import os
import zipfile

def zip_project():
    workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    zip_path = os.path.join(workspace, "smart_liquidity_clean.zip")
    
    # Exclude list
    exclude_dirs = {"venv", ".git", "__pycache__", "smart_liquidity_ai", ".agents", ".gemini"}
    exclude_files = {
        "smart_liquidity_ai.zip", 
        "smart_liquidity_v2.zip", 
        "smart_liquidity_clean.zip", 
        "smart_liquidity.db"
    }
    
    print(f"Creating clean ZIP archive at: {zip_path}")
    
    count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(workspace):
            # Modify dirs in-place to skip excluded directories recursively
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files:
                    continue
                if file.endswith(".pyc") or file.endswith(".db"):
                    continue
                    
                file_path = os.path.join(root, file)
                # Store path relative to workspace
                arcname = os.path.relpath(file_path, workspace)
                zipf.write(file_path, arcname)
                count += 1
                
    print(f"ZIP creation successful! Packaged {count} files.")
    print(f"File size: {os.path.getsize(zip_path) / 1024:.2f} KB")

if __name__ == "__main__":
    zip_project()
