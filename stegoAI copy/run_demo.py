import subprocess
import os
import sys

def run_command(command):
    print(f"\n[DEMO] Running: {command}")
    try:
        # Use shell=True to handle arguments correctly on Windows
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed with exit code {e.returncode}")
        print(e.stderr)
        return False
    return True

def main():
    python_exe = "py -3.11" # Force python 3.11

    print("=== STARTING DEEP VIDEO STEGANOGRAPHY DEMO ===\n")

    # 1. Image Hiding
    print("--- 1. Hiding Image ---")
    cmd_hide_img = f"{python_exe} image_hide.py --model models/hide.h5 --secret_image test/secret.png --cover_image test/cover.png"
    if run_command(cmd_hide_img):
        if os.path.exists("test/container.png"):
            print("[SUCCESS] Created test/container.png")
        else:
            print("[FAILURE] Output file test/container.png not found.")

    # 2. Image Revealing
    print("\n--- 2. Revealing Image ---")
    cmd_reveal_img = f"{python_exe} image_reveal.py --model models/reveal.h5 --container_image test/container.png"
    if run_command(cmd_reveal_img):
        if os.path.exists("test/secretout.png"):
            print("[SUCCESS] Created test/secretout.png")
        else:
            print("[FAILURE] Output file test/secretout.png not found.")

    # 3. Video Hiding
    print("\n--- 3. Hiding Video ---")
    # Ensure output directory exists
    os.makedirs("results", exist_ok=True)
    cmd_hide_vid = f"{python_exe} video_hide.py --model models/hide.h5 --secret_video videos/secret.mp4 --cover_video videos/cover.mp4"
    if run_command(cmd_hide_vid):
         if os.path.exists("results/cover_outvid_224.avi"):
            print("[SUCCESS] Created results/cover_outvid_224.avi")
         else:
            print("[FAILURE] Output file results/cover_outvid_224.avi not found.")

    # 4. Video Revealing
    print("\n--- 4. Revealing Video ---")
    cmd_reveal_vid = f"{python_exe} video_reveal.py --model models/reveal.h5 --container_video results/cover_outvid_224.avi"
    if run_command(cmd_reveal_vid):
         if os.path.exists("results/secret_outvid_300.avi"):
            print("[SUCCESS] Created results/secret_outvid_300.avi")
         else:
            print("[FAILURE] Output file results/secret_outvid_300.avi not found.")

    print("\n=== DEMO COMPLETED ===")

if __name__ == "__main__":
    main()
