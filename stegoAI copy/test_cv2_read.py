import cv2
import os

files = ['videos/secret.mp4', 'videos/cover.mp4']

for f in files:
    if not os.path.exists(f):
        print(f"[ERROR] {f} does not exist")
        continue
    
    cap = cv2.VideoCapture(f)
    if not cap.isOpened():
        print(f"[ERROR] Could not open {f}")
    else:
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"[SUCCESS] Opened {f}, frames: {count}")
        ret, frame = cap.read()
        if ret:
            print(f"Read frame shape: {frame.shape}")
        else:
            print("Failed to read first frame")
    cap.release()
