import os
import subprocess
import sys

def run_command(command):
    print(f"\n[RUNNING] {command}")
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Execution failed with code {e.returncode}")

def get_path(prompt):
    while True:
        path = input(prompt).strip()
        # Remove quotes if user copied as path
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        if os.path.exists(path):
            return path
        print(f"[ERROR] File not found: {path}")

def main():
    python_exe = "py -3.11"
    
    print("=== Deep Video Steganography: Custom Data Tester ===")
    print("1. Hide Image")
    print("2. Reveal Image")
    print("3. Hide Video")
    print("4. Reveal Video")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == '1':
        print("\n--- Hiding Custom Image ---")
        secret = get_path("Enter path to SECRET image: ")
        cover = get_path("Enter path to COVER image: ")
        output_name = input("Enter output filename (default: custom_container.png): ").strip() or "custom_container.png"
        output_path = os.path.join("results", output_name)
        os.makedirs("results", exist_ok=True)
        
        # Note: image_hide.py hardcodes output to test/container.png currently
        # We will run it, then move the file
        cmd = f"{python_exe} image_hide.py --model models/hide.h5 --secret_image \"{secret}\" --cover_image \"{cover}\""
        run_command(cmd)
        
        if os.path.exists("test/container.png"):
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename("test/container.png", output_path)
            print(f"\n[SUCCESS] Container image saved to: {output_path}")
            
    elif choice == '2':
        print("\n--- Revealing Custom Image ---")
        container = get_path("Enter path to CONTAINER image: ")
        output_name = input("Enter output filename (default: custom_secret_out.png): ").strip() or "custom_secret_out.png"
        output_path = os.path.join("results", output_name)
        
        # image_reveal.py hardcodes output to test/secretout.png
        cmd = f"{python_exe} image_reveal.py --model models/reveal.h5 --container_image \"{container}\""
        run_command(cmd)
        
        if os.path.exists("test/secretout.png"):
             if os.path.exists(output_path):
                os.remove(output_path)
             os.rename("test/secretout.png", output_path)
             print(f"\n[SUCCESS] Secret image revealed to: {output_path}")

    elif choice == '3':
        print("\n--- Hiding Custom Video ---")
        secret = get_path("Enter path to SECRET video: ")
        cover = get_path("Enter path to COVER video: ")
        
        # video_hide.py hardcodes output to results/cover_outvid_224.avi
        cmd = f"{python_exe} video_hide.py --model models/hide.h5 --secret_video \"{secret}\" --cover_video \"{cover}\""
        run_command(cmd)
        
        if os.path.exists("results/cover_outvid_224.avi"):
            print(f"\n[SUCCESS] Container video saved to: results/cover_outvid_224.avi")

    elif choice == '4':
        print("\n--- Revealing Custom Video ---")
        container = get_path("Enter path to CONTAINER video: ")
        
        # video_reveal.py hardcodes output to results/secret_outvid_300.avi
        cmd = f"{python_exe} video_reveal.py --model models/reveal.h5 --container_video \"{container}\""
        run_command(cmd)
        
        if os.path.exists("results/secret_outvid_300.avi"):
            print(f"\n[SUCCESS] Secret video revealed to: results/secret_outvid_300.avi")
            
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
