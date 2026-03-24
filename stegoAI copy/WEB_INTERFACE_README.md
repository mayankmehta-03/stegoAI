# 🛡️ StegoAI - Web Interface

A professional web-based interface for image and video steganography using deep neural networks. Hide secret images inside cover images/videos and extract them with state-of-the-art neural encoding!

## ✨ Features

### 🖼️ **Hide Secret Image in Image**
- Upload a cover image and secret image
- Advanced neural network encodes the secret data
- Optional block shuffling for enhanced security
- Download the container image with hidden secret

### 🎥 **Hide Secret Image in Video**
- Hide secret image in video frames
- Processes all video frames with neural encoding
- Supports MP4, AVI, MOV, MKV formats
- Download the processed video

### 🔍 **Reveal Secret from Image**
- Extract hidden secret from container image
- Uses reveal neural network
- Optional block shuffling for decryption
- Preview and download extracted secret

### 🎬 **Reveal Secret from Video**
- Extract hidden secret from specific video frame
- Select frame number to extract from
- View frame count automatically
- Download extracted secret image

### 🔒 **Enhanced Security**
- Optional block shuffling encryption
- Deep learning-based encoding
- Imperceptible to the human eye
- Robust against common attacks

---

## 📋 Requirements

- Python 3.7+
- TensorFlow/Keras
- Flask
- OpenCV
- Pillow
- ImageIO
- Scikit-image

---

## 🚀 Installation & Setup

### 1. **Activate Virtual Environment**
```bash
# On Windows
.venv\Scripts\Activate.ps1

# On Linux/Mac
source .venv/bin/activate
```

### 2. **Install Dependencies**
```bash
pip install -r requirements_web.txt
```

### 3. **Verify Model Files**
Make sure the following files exist:
- `models/hide.h5` - Neural network for hiding secrets
- `models/reveal.h5` - Neural network for revealing secrets

If not present, train them using:
```bash
python train.py
```

---

## 🎯 Running the Web Interface

### Start the Flask Server
```bash
python app.py
```

### Access the Interface
Open your browser and navigate to:
```
http://localhost:5000
```

The interface will be available immediately with a modern, user-friendly design.

---

## 🎨 Interface Walkthrough

### Tab 1: Hide Image in Image
1. **Upload Cover Image**: Drag or click to upload your cover image (PNG, JPG, BMP)
2. **Upload Secret Image**: Upload the image you want to hide
3. **Toggle Security**: Enable/disable block shuffling for enhanced security
4. **Click Hide Button**: The neural network will encode the secret into the cover
5. **Download**: Get your container image with the hidden secret

### Tab 2: Hide Image in Video
1. **Upload Cover Video**: Provide a video file (MP4, AVI, MOV, MKV)
2. **Upload Secret Image**: Upload the image to hide in all frames
3. **Toggle Security**: Optional block shuffling
4. **Click Hide Button**: Wait for processing (longer videos take more time)
5. **Download**: Get the video with hidden secrets in every frame

### Tab 3: Reveal Image from Image
1. **Upload Container Image**: Upload image with hidden secret
2. **Toggle Security**: Must match the encryption used during hiding
3. **Click Reveal Button**: The neural network extracts the secret
4. **Download**: Get the revealed secret image

### Tab 4: Reveal Image from Video
1. **Upload Container Video**: Provide video with hidden secrets
2. **Frame Selection**: Choose which frame to extract from (auto-populated)
3. **Toggle Security**: Must match the encryption used during hiding
4. **Click Reveal Button**: Extract secret from selected frame
5. **Download**: Get the revealed secret image

---

## 📊 File Organization

```
stegoAI/
├── app.py                    # Flask application
├── requirements_web.txt      # Python dependencies
├── models/
│   ├── hide.h5              # Hide neural network model
│   └── reveal.h5            # Reveal neural network model
├── static/
│   ├── css/
│   │   └── style.css        # Web interface styling
│   └── js/
│       └── app.js           # Frontend logic & interactions
├── templates/
│   └── index.html           # Main HTML template
├── uploads/                 # Temporary uploaded files
└── output/                  # Processed results
```

---

## 🔧 Advanced Configuration

### Adjust File Upload Limits
Edit `app.py` and modify:
```python
MAX_FILE_SIZE = 500 * 1024 * 1024  # Default: 500 MB
```

### Change Server Settings
```python
if __name__ == '__main__':
    app.run(
        debug=True,              # Set to False for production
        host='0.0.0.0',         # Listen on all interfaces
        port=5000               # Change port if needed
    )
```

### Configure Block Shuffling
The block size for security shuffling is set to 56 pixels:
```python
BLOCK_SIZE = 56  # Adjust if needed
```

---

## 🎓 How It Works

### Encoding Process
1. **Image Preparation**: Both images resized to 256×256 and normalized
2. **Block Shuffling** (optional): Pixels rearranged in 56×56 blocks for security
3. **Neural Encoding**: Hide model fuses cover and secret through deep convolutional layers
4. **Output Generation**: Container image with imperceptibly encoded secret

### Decoding Process
1. **Image Preparation**: Container resized and normalized
2. **Block Unshuffling** (optional): Reverse the shuffling
3. **Neural Decoding**: Reveal model extracts secret information
4. **Image Recovery**: Secret image reconstructed from neural outputs

---

## 📁 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Load web interface |
| `/api/upload` | POST | Upload file |
| `/api/hide-image` | POST | Hide image in image |
| `/api/hide-video` | POST | Hide image in video |
| `/api/reveal-image` | POST | Reveal from image |
| `/api/reveal-video` | POST | Reveal from video |
| `/api/status/<id>` | GET | Check processing status |
| `/api/download/<file>` | GET | Download result |
| `/api/preview/<file>` | GET | Preview result image |
| `/api/video-info/<file>` | GET | Get video frame count |

---

## ⚠️ Important Notes

### Security Considerations
- Always use the same security settings (shuffling) for hiding and revealing
- Keep model files (`hide.h5`, `reveal.h5`) in the correct location
- For production, disable debug mode and use HTTPS
- Temporary files in `uploads/` are not automatically cleaned (implement if needed)

### Perfect Reconstruction
- Use matching image dimensions (preferably 256×256)
- Maintain consistent color space (RGB)
- Don't compress container images after hiding (use PNG, not JPEG)
- Apply same security settings for hide and reveal

### Performance
- Image processing: Usually <5 seconds
- Video processing: Depends on frame count and video duration
- First run loads models: Takes 5-10 seconds
- Subsequent operations: Much faster due to cached models

---

## 🐛 Troubleshooting

### Models Not Loading
```
Error: Model not loaded
```
**Solution**: Ensure `models/hide.h5` and `models/reveal.h5` exist and train if necessary.

### Port Already in Use
```
Address already in use
```
**Solution**: Change port in `app.py` or close previous Flask instance:
```bash
# Find process using port 5000
netstat -ano | findstr :5000
# Kill it (Windows)
taskkill /PID <PID> /F
```

### File Upload Issues
- Check file size (max 500 MB)
- Verify file format (PNG, JPG, BMP for images; MP4, AVI, MOV for videos)
- Ensure downloads folder has write permissions

### Memory Issues with Large Videos
- Process shorter videos
- Reduce frame sampling
- Run on machine with more RAM

---

## 🚀 Deployment

### For Production
1. Set `debug=False` in `app.py`
2. Use production WSGI server:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

3. Enable HTTPS with SSL certificates
4. Implement file cleanup mechanism
5. Add rate limiting for API endpoints
6. Use reverse proxy (Nginx, Apache)

---

## 📝 Example Usage Flow

### Hiding a Secret
1. Start Flask server: `python app.py`
2. Open http://localhost:5000
3. Click "Hide in Image" tab
4. Upload `cat.png` as cover
5. Upload `secret.png` as secret
6. Enable shuffling for security
7. Click "Hide Secret Image"
8. Wait for processing
9. Download `hidden_xxx.png`

### Revealing a Secret
1. Click "Reveal from Image" tab
2. Upload the `hidden_xxx.png` file
3. **Important**: Enable shuffling (must match!)
4. Click "Reveal Secret Image"
5. Download the recovered secret image

---

## 📊 Supported Formats

### Images
- ✅ PNG
- ✅ JPG/JPEG
- ✅ BMP

### Videos
- ✅ MP4
- ✅ AVI
- ✅ MOV
- ✅ MKV

---

## 📜 License

This project is part of the StegoAI steganography suite.

---

## 🤝 Support

For issues or questions:
1. Check the Troubleshooting section
2. Verify model files are present
3. Check Python and dependency versions
4. Review Flask console output for detailed error messages

---

## ✅ Checklist Before Running

- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip install -r requirements_web.txt`)
- [ ] Model files present (`models/hide.h5`, `models/reveal.h5`)
- [ ] `templates/` and `static/` folders exist with files
- [ ] Port 5000 is available
- [ ] Write permissions for `uploads/` and `output/` directories

---

**Ready to protect your secrets with AI? 🚀**

Start the server and begin steganography!
