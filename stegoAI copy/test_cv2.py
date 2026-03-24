import cv2
import numpy as np
import os

filename = 'test_video.avi'
frame = np.zeros((224, 224, 3), dtype=np.uint8)
# Try MJPG
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
out = cv2.VideoWriter(filename, fourcc, 15, (224, 224))

if not out.isOpened():
    print("Error: VideoWriter not opened")
else:
    for _ in range(30):
        out.write(frame)
    out.release()
    print(f"Created {filename}, size: {os.path.getsize(filename)}")
