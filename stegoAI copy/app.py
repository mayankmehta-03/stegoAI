from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename
import os
import numpy as np
from PIL import Image
import cv2
import imageio
from keras.models import load_model
import threading
from datetime import datetime
import io
from skimage.util.shape import view_as_blocks
import traceback

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'output')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'mp4', 'avi', 'mov', 'mkv'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
BLOCK_SIZE = 56

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create necessary folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Load models at startup
try:
    # Image steganography models (original)
    hide_model = load_model('models/hide.h5', compile=False)
    reveal_model = load_model('models/reveal.h5', compile=False)
    print("✓ Image models loaded successfully")
except Exception as e:
    print(f"✗ Error loading image models: {e}")
    hide_model = None
    reveal_model = None

# Use the SAME proven image models for video operations (video = sequence of image frames)
# The image models are deep, well-trained autoencoders that produce crystal-clear results.
# Our custom-trained video models were too shallow — using the image models is the correct approach.
video_hide_model = hide_model
video_reveal_model = reveal_model
print("✓ Using proven image models for video operations (autoencoder/decoder)")

# Processing status tracker
processing_status = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def normalize_batch(imgs):
    """Performs channel-wise z-score normalization"""
    return (imgs - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])

def denormalize_batch(imgs, should_clip=True):
    """Denormalize images"""
    imgs = (imgs * np.array([0.229, 0.224, 0.225])) + np.array([0.485, 0.456, 0.406])
    if should_clip:
        imgs = np.clip(imgs, 0, 1)
    return imgs

def shuffle_blocks(im, inverse=False):
    """Custom block shuffling for enhanced security"""
    try:
        blk_size = BLOCK_SIZE
        rows = np.uint8(im.shape[0] / blk_size)
        cols = np.uint8(im.shape[1] / blk_size)
        
        img_blks = view_as_blocks(im, block_shape=(blk_size, blk_size, 3)).squeeze()
        img_shuff = np.zeros((im.shape[0], im.shape[1], 3), dtype=np.uint8)
        
        shuffle_map = {0: 2, 1: 0, 2: 3, 3: 1}
        inv_map = {v: k for k, v in shuffle_map.items()}
        
        target_map = inv_map if inverse else shuffle_map
        
        for i in range(rows):
            for j in range(cols):
                shuffled_i, shuffled_j = divmod(target_map[i * 2 + j // 2], 2), (target_map[i * 2 + j // 2] % 2)
                img_shuff[shuffled_i * blk_size:(shuffled_i + 1) * blk_size,
                          shuffled_j * blk_size:(shuffled_j + 1) * blk_size] = img_blks[i, j]
        
        return img_shuff
    except Exception as e:
        print(f"Shuffling error: {e}")
        return im

def process_image_for_hiding(image_path):
    """Process and prepare image for hiding"""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (224, 224))  # Model trained on 224x224
        img = np.float32(img) / 255.0
        return img
    except Exception as e:
        print(f"Image processing error: {e}")
        return None

def process_video_frames(video_path, max_frames=None, session_id=None, progress_start=10, progress_end=15):
    """Extract frames from video with progress tracking - supports imageio and OpenCV"""
    try:
        print(f"[process_video_frames] Opening video (imageio): {video_path}")
        vid = imageio.get_reader(video_path)
        print(f"[process_video_frames] Video opened successfully (imageio)")
        
        frames = []
        frame_count = 0
        for i, frame in enumerate(vid):
            if max_frames and i >= max_frames:
                print(f"[process_video_frames] Reached max_frames limit: {max_frames}")
                break
            # imageio already returns frames in RGB format — no color conversion needed!
            # (cv2.cvtColor BGR2RGB was incorrectly swapping Red↔Blue channels)
            frame = cv2.resize(frame, (224, 224))  # Model trained on 224x224
            frames.append(np.float32(frame) / 255.0)
            frame_count += 1
            
            # Update progress during frame extraction
            if session_id and (frame_count % 5 == 0):
                progress = progress_start + int((frame_count / (max_frames or 50)) * (progress_end - progress_start))
                processing_status[session_id] = {"status": "loading_frames", "progress": min(progress, progress_end)}
            
            if frame_count % 10 == 0:
                print(f"[process_video_frames] Extracted {frame_count} frames...")
        
        # If no frames extracted, imageio might have failed silently
        if len(frames) == 0:
            print(f"[process_video_frames] WARNING: imageio returned 0 frames, trying OpenCV fallback...")
            return process_video_frames_opencv(video_path, max_frames, session_id, progress_start, progress_end)
        
        print(f"[process_video_frames] Total frames extracted: {len(frames)}")
        return np.array(frames)
    except Exception as e:
        print(f"[process_video_frames] imageio ERROR: {e}")
        print(f"[process_video_frames] Trying OpenCV fallback...")
        return process_video_frames_opencv(video_path, max_frames, session_id, progress_start, progress_end)

def process_video_frames_opencv(video_path, max_frames=None, session_id=None, progress_start=10, progress_end=15):
    """Fallback: Extract frames using OpenCV"""
    try:
        print(f"[process_video_frames_opencv] Opening video: {video_path}")
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"[process_video_frames_opencv] ERROR: Could not open video")
            return None
        
        print(f"[process_video_frames_opencv] Video opened successfully")
        
        frames = []
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if max_frames and frame_count >= max_frames:
                print(f"[process_video_frames_opencv] Reached max_frames limit: {max_frames}")
                break
            
            # Convert BGR to RGB and resize
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (224, 224))
            frames.append(np.float32(frame) / 255.0)
            frame_count += 1
            
            # Update progress during frame extraction
            if session_id and (frame_count % 5 == 0):
                progress = progress_start + int((frame_count / (max_frames or 50)) * (progress_end - progress_start))
                processing_status[session_id] = {"status": "loading_frames", "progress": min(progress, progress_end)}
            
            if frame_count % 10 == 0:
                print(f"[process_video_frames_opencv] Extracted {frame_count} frames...")
        
        cap.release()
        print(f"[process_video_frames_opencv] Total frames extracted: {len(frames)}")
        return np.array(frames)
    except Exception as e:
        print(f"[process_video_frames_opencv] ERROR: {e}")
        traceback.print_exc()
        return None

def hide_image_in_image(cover_path, secret_path, session_id, use_shuffle=False):
    """Hide secret image inside cover image"""
    try:
        if not hide_model:
            return None, "Model not loaded"
        
        processing_status[session_id] = {"status": "loading_images", "progress": 10}
        
        # Load and prepare images
        cover_img = process_image_for_hiding(cover_path)
        secret_img = process_image_for_hiding(secret_path)
        
        if cover_img is None or secret_img is None:
            return None, "Failed to process images"
        
        processing_status[session_id] = {"status": "shuffling", "progress": 30}
        
        if use_shuffle:
            cover_img = shuffle_blocks(cover_img)
            secret_img = shuffle_blocks(secret_img)
        
        processing_status[session_id] = {"status": "encoding", "progress": 50}
        
        # Prepare batch for model - add batch dimension only (model expects shape (1, 224, 224, 3))
        cover_batch = np.expand_dims(cover_img, 0)  # (1, 224, 224, 3)
        secret_batch = np.expand_dims(secret_img, 0)  # (1, 224, 224, 3)
        cover_batch = normalize_batch(cover_batch)
        secret_batch = normalize_batch(secret_batch)
        
        # Generate container - model expects [secret, cover] as separate inputs
        container = hide_model.predict([secret_batch, cover_batch], verbose=0)
        container = denormalize_batch(container)
        container = np.squeeze(container)
        
        processing_status[session_id] = {"status": "saving", "progress": 90}
        
        # Save result
        output_path = os.path.join(OUTPUT_FOLDER, f"hidden_{session_id}.png")
        container_uint8 = np.uint8(np.clip(container * 255, 0, 255))
        Image.fromarray(container_uint8).save(output_path)
        
        # Get just the filename without path
        output_filename = os.path.basename(output_path)
        processing_status[session_id] = {"status": "completed", "progress": 100, "filename": output_filename}
        
        return output_path, "Success"
    
    except Exception as e:
        processing_status[session_id] = {"status": "error", "error": str(e)}
        return None, str(e)

def hide_video_in_video(cover_path, secret_path, session_id, use_shuffle=False):
    """Hide secret video inside cover video"""
    try:
        if not hide_model:
            processing_status[session_id] = {"status": "error", "error": "Model not loaded"}
            return None, "Model not loaded"
        
        processing_status[session_id] = {"status": "processing_video", "progress": 10}
        print(f"[{session_id}] Starting video-in-video encoding...")
        print(f"[{session_id}] Cover video: {cover_path}")
        print(f"[{session_id}] Secret video: {secret_path}")
        
        # Verify files exist
        if not os.path.exists(cover_path):
            error_msg = f"Cover video not found: {cover_path}"
            print(f"[{session_id}] ERROR: {error_msg}")
            processing_status[session_id] = {"status": "error", "error": error_msg}
            return None, error_msg
        
        if not os.path.exists(secret_path):
            error_msg = f"Secret video not found: {secret_path}"
            print(f"[{session_id}] ERROR: {error_msg}")
            processing_status[session_id] = {"status": "error", "error": error_msg}
            return None, error_msg
        
        # Extract frames from both videos (limited to 1000 frames = ~33.3 seconds at 30fps)
        # Batch processing optimized for GTX 1650 Ti - processes 10 frames at once (3-5x faster)
        MAX_FRAMES = 1000
        processing_status[session_id] = {"status": "loading_frames", "progress": 15}
        print(f"[{session_id}] Extracting cover video frames (max {MAX_FRAMES})...")
        cover_frames = process_video_frames(cover_path, max_frames=MAX_FRAMES, session_id=session_id, progress_start=15, progress_end=22)
        
        processing_status[session_id] = {"status": "loading_frames", "progress": 22}
        print(f"[{session_id}] Extracting secret video frames (max {MAX_FRAMES})...")
        secret_frames = process_video_frames(secret_path, max_frames=MAX_FRAMES, session_id=session_id, progress_start=22, progress_end=25)
        
        if cover_frames is None or secret_frames is None:
            error_msg = "Failed to extract video frames"
            print(f"[{session_id}] {error_msg}")
            processing_status[session_id] = {"status": "error", "error": error_msg}
            return None, error_msg
        
        # Ensure same frame count by padding or truncating
        min_frames = min(len(cover_frames), len(secret_frames))
        cover_frames = cover_frames[:min_frames]
        secret_frames = secret_frames[:min_frames]
        
        print(f"[{session_id}] Loaded {len(cover_frames)} cover frames and {len(secret_frames)} secret frames")
        print(f"[{session_id}] Using {min_frames} frames for encoding...")
        processing_status[session_id] = {"status": "encoding_frames", "progress": 25}
        
        container_frames = []
        total_frames = len(cover_frames)
        BATCH_SIZE = 10  # Process 10 frames at once for 3-5x speedup
        
        # Process frames in batches for faster GPU utilization
        for batch_start in range(0, total_frames, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_frames)
            batch_size = batch_end - batch_start
            
            # Extract batch of frames
            cover_batch_frames = cover_frames[batch_start:batch_end]
            secret_batch_frames = secret_frames[batch_start:batch_end]
            
            # Apply shuffling if needed
            if use_shuffle:
                cover_batch_frames = [shuffle_blocks(f) for f in cover_batch_frames]
                secret_batch_frames = [shuffle_blocks(f) for f in secret_batch_frames]
            
            # Stack into batch (batch_size, 224, 224, 3)
            cover_batch = np.array(cover_batch_frames)
            secret_batch = np.array(secret_batch_frames)
            cover_batch = normalize_batch(cover_batch)
            secret_batch = normalize_batch(secret_batch)
            
            # Process entire batch through model at once (much faster!)
            containers = video_hide_model.predict([secret_batch, cover_batch], verbose=0)
            containers = denormalize_batch(containers)
            
            # Extract individual frames from batch result
            for i in range(batch_size):
                container_uint8 = np.uint8(np.clip(containers[i] * 255, 0, 255))
                container_frames.append(container_uint8)
            
            # Update progress
            progress = 25 + int((batch_end / total_frames) * 55)
            processing_status[session_id] = {"status": "encoding_frames", "progress": progress}
            print(f"[{session_id}] Encoded {batch_end}/{total_frames} frames (progress: {progress}%)")
        
        print(f"[{session_id}] All frames encoded. Saving encrypted video...")
        processing_status[session_id] = {"status": "saving", "progress": 85}
        
        # Save encrypted video — MUST use LOSSLESS codec to preserve hidden steganographic data!
        # Lossy H.264/MP4 destroys the subtle pixel perturbations that encode the secret.
        # This is exactly like how image steganography uses lossless PNG instead of lossy JPEG.
        output_path = os.path.join(OUTPUT_FOLDER, f"hidden_{session_id}.avi")
        print(f"[{session_id}] Writing {len(container_frames)} frames to {output_path} (LOSSLESS)")
        
        try:
            # Use FFV1 lossless codec in AVI container — preserves every single pixel
            writer = imageio.get_writer(output_path, fps=30, codec='ffv1', pixelformat='bgr24')
            for frame_idx, frame in enumerate(container_frames):
                writer.append_data(frame)
                if (frame_idx + 1) % max(1, len(container_frames) // 5) == 0:
                    print(f"[{session_id}] Written {frame_idx + 1}/{len(container_frames)} frames")
            writer.close()
            print(f"[{session_id}] Video saved successfully (LOSSLESS FFV1)")
        except Exception as write_error:
            print(f"[{session_id}] FFV1 codec failed ({write_error}), trying rawvideo...")
            try:
                output_path = os.path.join(OUTPUT_FOLDER, f"hidden_{session_id}.avi")
                writer = imageio.get_writer(output_path, fps=30, codec='rawvideo', pixelformat='bgr24')
                for frame in container_frames:
                    writer.append_data(frame)
                writer.close()
                print(f"[{session_id}] Video saved with rawvideo codec (LOSSLESS)")
            except Exception as fallback_error:
                print(f"[{session_id}] rawvideo also failed ({fallback_error}), trying PNG sequence...")
                # Ultimate fallback: save as individual PNG frames in a folder
                import shutil
                frames_dir = os.path.join(OUTPUT_FOLDER, f"hidden_{session_id}_frames")
                os.makedirs(frames_dir, exist_ok=True)
                for idx, frame in enumerate(container_frames):
                    Image.fromarray(frame).save(os.path.join(frames_dir, f"frame_{idx:06d}.png"))
                output_path = frames_dir
                print(f"[{session_id}] Saved as PNG frames (LOSSLESS)")
        
        output_filename = os.path.basename(output_path)
        processing_status[session_id] = {"status": "completed", "progress": 100, "filename": output_filename}
        print(f"[{session_id}] Processing complete. Filename: {output_filename}")
        
        return output_path, "Success"
    
    except Exception as e:
        print(f"[{session_id}] Error: {str(e)}")
        processing_status[session_id] = {"status": "error", "error": str(e)}
        traceback.print_exc()
        return None, str(e)

def reveal_image_from_image(container_path, session_id, use_shuffle=False):
    """Reveal secret image from container image"""
    try:
        if not reveal_model:
            return None, "Model not loaded"
        
        processing_status[session_id] = {"status": "loading", "progress": 10}
        
        # Load and prepare image
        container_img = process_image_for_hiding(container_path)
        if container_img is None:
            return None, "Failed to load image"
        
        processing_status[session_id] = {"status": "decoding", "progress": 40}
        
        if use_shuffle:
            container_img = shuffle_blocks(container_img, inverse=True)
        
        # Prepare batch - add batch dimension only (model expects shape (1, 224, 224, 3))
        container_batch = np.expand_dims(container_img, 0)  # (1, 224, 224, 3)
        container_batch = normalize_batch(container_batch)
        
        # Extract secret
        secret = reveal_model.predict(container_batch, verbose=0)
        secret = denormalize_batch(secret)
        secret = np.squeeze(secret)
        
        processing_status[session_id] = {"status": "saving", "progress": 90}
        
        # Save result
        output_path = os.path.join(OUTPUT_FOLDER, f"revealed_{session_id}.png")
        secret_uint8 = np.uint8(np.clip(secret * 255, 0, 255))
        Image.fromarray(secret_uint8).save(output_path)
        
        # Get just the filename without path
        output_filename = os.path.basename(output_path)
        processing_status[session_id] = {"status": "completed", "progress": 100, "filename": output_filename}
        
        return output_path, "Success"
    
    except Exception as e:
        processing_status[session_id] = {"status": "error", "error": str(e)}
        return None, str(e)

def reveal_image_from_video(container_path, session_id, frame_number=0, use_shuffle=False):
    """Extract and reveal secret from specific video frame"""
    try:
        if not reveal_model:
            return None, "Model not loaded"
        
        processing_status[session_id] = {"status": "loading_video", "progress": 10}
        
        # Extract frame
        vid = imageio.get_reader(container_path)
        frames = []
        for i, frame in enumerate(vid):
            if i == frame_number:
                frames.append(frame)
                break
            if i > frame_number:  # Stop if we've gone past the desired frame
                break
        
        if not frames:
            return None, f"Frame {frame_number} not available"
        
        frame = frames[0]
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (224, 224))  # Model trained on 224x224
        container_img = np.float32(frame) / 255.0
        
        processing_status[session_id] = {"status": "decoding", "progress": 40}
        
        if use_shuffle:
            container_img = shuffle_blocks(container_img, inverse=True)
        
        # Prepare batch - add batch dimension only (model expects shape (1, 224, 224, 3))
        container_batch = np.expand_dims(container_img, 0)  # (1, 224, 224, 3)
        container_batch = normalize_batch(container_batch)
        
        # Extract secret
        secret = reveal_model.predict(container_batch, verbose=0)
        secret = denormalize_batch(secret)
        secret = np.squeeze(secret)
        
        processing_status[session_id] = {"status": "saving", "progress": 90}
        
        # Save result
        output_path = os.path.join(OUTPUT_FOLDER, f"revealed_{session_id}.png")
        secret_uint8 = np.uint8(np.clip(secret * 255, 0, 255))
        Image.fromarray(secret_uint8).save(output_path)
        
        # Get just the filename without path
        output_filename = os.path.basename(output_path)
        processing_status[session_id] = {"status": "completed", "progress": 100, "filename": output_filename}
        
        return output_path, "Success"
    
    except Exception as e:
        processing_status[session_id] = {"status": "error", "error": str(e)}
        traceback.print_exc()
        return None, str(e)

def reveal_video_from_video(container_path, session_id, use_shuffle=False):
    """Extract secret video from encrypted video"""
    try:
        if not reveal_model:
            processing_status[session_id] = {"status": "error", "error": "Model not loaded"}
            return None, "Model not loaded"
        
        processing_status[session_id] = {"status": "loading_video", "progress": 10}
        print(f"[{session_id}] Loading encrypted video...")
        
        # Extract frames from encrypted video (limited to 1000 frames = ~33.3 seconds)
        container_frames = process_video_frames(container_path, max_frames=1000, session_id=session_id, progress_start=10, progress_end=25)
        
        if container_frames is None or len(container_frames) == 0:
            error_msg = "Failed to extract frames from video"
            processing_status[session_id] = {"status": "error", "error": error_msg}
            return None, error_msg
        
        print(f"[{session_id}] Extracted {len(container_frames)} frames. Starting decoding...")
        processing_status[session_id] = {"status": "decoding_frames", "progress": 25}
        
        secret_frames = []
        total_frames = len(container_frames)
        BATCH_SIZE = 10  # Process 10 frames at once for 3-5x speedup
        
        # Process frames in batches for faster GPU utilization
        for batch_start in range(0, total_frames, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_frames)
            batch_size = batch_end - batch_start
            
            # Extract batch of frames
            batch_frames = container_frames[batch_start:batch_end]
            
            # Apply inverse shuffling if needed
            if use_shuffle:
                batch_frames = [shuffle_blocks(f, inverse=True) for f in batch_frames]
            
            # Stack into batch (batch_size, 224, 224, 3)
            container_batch = np.array(batch_frames)
            container_batch = normalize_batch(container_batch)
            
            # Process entire batch through model at once (much faster!)
            secrets = video_reveal_model.predict(container_batch, verbose=0)
            secrets = denormalize_batch(secrets)
            
            # Extract individual frames from batch result with color enhancement
            for i in range(batch_size):
                frame = secrets[i]
                
                # Per-channel contrast stretching to restore full color vibrancy
                # The hide/reveal cycle slightly compresses the dynamic range
                for ch in range(3):
                    ch_min = frame[:,:,ch].min()
                    ch_max = frame[:,:,ch].max()
                    if ch_max - ch_min > 0.01:  # Avoid division by zero
                        frame[:,:,ch] = (frame[:,:,ch] - ch_min) / (ch_max - ch_min)
                
                secret_uint8 = np.uint8(np.clip(frame * 255, 0, 255))
                secret_frames.append(secret_uint8)
            
            # Update progress
            progress = 25 + int((batch_end / total_frames) * 60)
            processing_status[session_id] = {"status": "decoding_frames", "progress": progress}
            print(f"[{session_id}] Decoded {batch_end}/{total_frames} frames (progress: {progress}%)")
        
        print(f"[{session_id}] All frames decoded. Saving secret video...")
        processing_status[session_id] = {"status": "saving", "progress": 85}
        
        # Save secret video
        output_path = os.path.join(OUTPUT_FOLDER, f"revealed_{session_id}.mp4")
        print(f"[{session_id}] Writing {len(secret_frames)} frames to {output_path}")
        
        try:
            # Use the same lossless codec for the revealed secret video
            writer = imageio.get_writer(output_path, fps=30, codec='ffv1', pixelformat='bgr24')
            for frame_idx, frame in enumerate(secret_frames):
                writer.append_data(frame)
                if (frame_idx + 1) % max(1, len(secret_frames) // 5) == 0:
                    print(f"[{session_id}] Written {frame_idx + 1}/{len(secret_frames)} frames")
            writer.close()
            print(f"[{session_id}] Video saved successfully")
        except Exception as write_error:
            print(f"[{session_id}] FFV1 failed ({write_error}), trying rawvideo...")
            try:
                writer = imageio.get_writer(output_path, fps=30, codec='rawvideo', pixelformat='bgr24')
                for frame in secret_frames:
                    writer.append_data(frame)
                writer.close()
                print(f"[{session_id}] Video saved with rawvideo codec")
            except Exception as fallback_error:
                print(f"[{session_id}] rawvideo also failed ({fallback_error}), trying default...")
                writer = imageio.get_writer(output_path, fps=30)
                for frame in secret_frames:
                    writer.append_data(frame)
                writer.close()
                print(f"[{session_id}] Video saved with default codec")
        
        output_filename = os.path.basename(output_path)
        processing_status[session_id] = {"status": "completed", "progress": 100, "filename": output_filename}
        print(f"[{session_id}] Processing complete. Filename: {output_filename}")
        
        return output_path, "Success"
    
    except Exception as e:
        print(f"[{session_id}] Error: {str(e)}")
        processing_status[session_id] = {"status": "error", "error": str(e)}
        traceback.print_exc()
        return None, str(e)

# Routes
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file uploads"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Save file
        filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Get file info
        file_size = os.path.getsize(filepath)
        ext = filename.rsplit('.', 1)[1].lower()
        is_video = ext in {'mp4', 'avi', 'mov', 'mkv'}
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'size': file_size,
            'is_video': is_video
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hide-image', methods=['POST'])
def hide_image():
    """Hide image in image"""
    try:
        data = request.json
        session_id = data.get('session_id')
        cover_path = data.get('cover_path')
        secret_path = data.get('secret_path')
        use_shuffle = data.get('use_shuffle', False)
        
        if not all([cover_path, secret_path, session_id]):
            return jsonify({'error': 'Missing required files'}), 400
        
        # Run in thread
        thread = threading.Thread(
            target=hide_image_in_image,
            args=(cover_path, secret_path, session_id, use_shuffle)
        )
        thread.start()
        
        return jsonify({'status': 'processing'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hide-video', methods=['POST'])
def hide_video():
    """Hide video in video"""
    try:
        data = request.json
        session_id = data.get('session_id')
        cover_path = data.get('cover_path')
        secret_path = data.get('secret_path')
        use_shuffle = data.get('use_shuffle', False)
        
        if not all([cover_path, secret_path, session_id]):
            return jsonify({'error': 'Missing required files'}), 400
        
        # Run in thread
        thread = threading.Thread(
            target=hide_video_in_video,
            args=(cover_path, secret_path, session_id, use_shuffle)
        )
        thread.start()
        
        return jsonify({'status': 'processing'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reveal-image', methods=['POST'])
def reveal_image():
    """Reveal image from image"""
    try:
        data = request.json
        session_id = data.get('session_id')
        container_path = data.get('container_path')
        use_shuffle = data.get('use_shuffle', False)
        
        if not all([container_path, session_id]):
            return jsonify({'error': 'Missing required file'}), 400
        
        # Run in thread
        thread = threading.Thread(
            target=reveal_image_from_image,
            args=(container_path, session_id, use_shuffle)
        )
        thread.start()
        
        return jsonify({'status': 'processing'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reveal-video', methods=['POST'])
def reveal_video():
    """Reveal video from encrypted video"""
    try:
        data = request.json
        session_id = data.get('session_id')
        container_path = data.get('container_path')
        use_shuffle = data.get('use_shuffle', False)
        
        if not all([container_path, session_id]):
            return jsonify({'error': 'Missing required file'}), 400
        
        # Run in thread
        thread = threading.Thread(
            target=reveal_video_from_video,
            args=(container_path, session_id, use_shuffle)
        )
        thread.start()
        
        return jsonify({'status': 'processing'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<session_id>')
def check_status(session_id):
    """Check processing status"""
    status = processing_status.get(session_id, {'status': 'not_found'})
    return jsonify(status)

@app.route('/api/download/<filename>')
def download_file(filename):
    """Download processed file"""
    try:
        filepath = os.path.join(OUTPUT_FOLDER, secure_filename(filename))
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview/<filename>')
def preview_file(filename):
    """Preview image file"""
    try:
        filepath = os.path.join(OUTPUT_FOLDER, secure_filename(filename))
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        return send_file(filepath, mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/video-info/<filename>')
def get_video_info(filename):
    """Get video frame count"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        vid = imageio.get_reader(filepath)
        frame_count = len(vid)
        return jsonify({'frame_count': frame_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting StegoAI Web Interface...")
    app.run(debug=True, host='0.0.0.0', port=5000)
