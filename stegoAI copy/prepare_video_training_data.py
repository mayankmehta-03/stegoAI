"""
Generate training data from video frames for steganography
This script extracts frames from videos and prepares them for model training
"""

import os
import cv2
import numpy as np
from pathlib import Path
import glob

# Configuration
VIDEOS_FOLDER = "videos"  # Path to your videos
OUTPUT_TRAIN = "dataset/train_data/train"
OUTPUT_VAL = "dataset/val_data/validation"
FRAMES_PER_VIDEO = 100  # Extract 100 frames per video for training
TARGET_SIZE = (224, 224)  # Model input size
SPLIT_RATIO = 0.8  # 80% train, 20% validation

def extract_frames_from_video(video_path, max_frames=FRAMES_PER_VIDEO):
    """Extract random frames from a video file"""
    frames = []
    try:
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames == 0:
            print(f"  ⚠️  No frames found in {os.path.basename(video_path)}")
            return frames
        
        # Calculate stride to evenly sample frames
        stride = max(1, total_frames // max_frames)
        frame_count = 0
        
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Resize and normalize
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, TARGET_SIZE)
            frames.append(frame)
            frame_count += 1
        
        cap.release()
        print(f"  ✓ Extracted {len(frames)} frames from {os.path.basename(video_path)}")
        return frames
    except Exception as e:
        print(f"  ✗ Error processing {video_path}: {e}")
        return frames

def generate_training_data():
    """Generate training data from videos"""
    
    print("\n" + "="*60)
    print("VIDEO-BASED TRAINING DATA GENERATION")
    print("="*60)
    
    # Create output directories
    os.makedirs(OUTPUT_TRAIN, exist_ok=True)
    os.makedirs(OUTPUT_VAL, exist_ok=True)
    
    # Find all video files
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.flv', '*.wmv']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(glob.glob(os.path.join(VIDEOS_FOLDER, ext)))
        # Also check in subdirectories
        video_files.extend(glob.glob(os.path.join(VIDEOS_FOLDER, '**', ext), recursive=True))
    
    if not video_files:
        print(f"\n⚠️  No video files found in '{VIDEOS_FOLDER}' directory")
        print("Please add video files first!")
        return False
    
    print(f"\n📹 Found {len(video_files)} video file(s)")
    
    all_frames = []
    
    # Extract frames from all videos
    print("\n[1/3] Extracting frames from videos...")
    for i, video_path in enumerate(video_files, 1):
        print(f"\n  [{i}/{len(video_files)}] Processing: {os.path.basename(video_path)}")
        frames = extract_frames_from_video(video_path, FRAMES_PER_VIDEO)
        all_frames.extend(frames)
    
    if not all_frames:
        print("\n✗ No frames extracted! Check your video files.")
        return False
    
    print(f"\n✓ Total frames extracted: {len(all_frames)}")
    
    # Normalize frames
    print("\n[2/3] Normalizing frames...")
    all_frames = np.array(all_frames, dtype=np.uint8)
    print(f"  ✓ Shape: {all_frames.shape}")
    
    # Split into train and validation
    print("\n[3/3] Saving training and validation data...")
    num_train = int(len(all_frames) * SPLIT_RATIO)
    
    train_indices = np.random.choice(len(all_frames), num_train, replace=False)
    val_indices = np.setdiff1d(np.arange(len(all_frames)), train_indices)
    
    # Save training frames
    train_count = 0
    for idx in train_indices:
        frame = all_frames[idx]
        filename = os.path.join(OUTPUT_TRAIN, f"frame_{train_count:06d}.png")
        cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        train_count += 1
    
    # Save validation frames
    val_count = 0
    for idx in val_indices:
        frame = all_frames[idx]
        filename = os.path.join(OUTPUT_VAL, f"frame_{val_count:06d}.png")
        cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        val_count += 1
    
    print(f"\n  ✓ Training frames: {train_count} → {OUTPUT_TRAIN}")
    print(f"  ✓ Validation frames: {val_count} → {OUTPUT_VAL}")
    
    print("\n" + "="*60)
    print("✅ TRAINING DATA READY!")
    print("="*60)
    print(f"\nNext step: Run 'python train.py' to retrain the model")
    print(f"Total training samples: {train_count + val_count}")
    
    return True

if __name__ == "__main__":
    generate_training_data()
