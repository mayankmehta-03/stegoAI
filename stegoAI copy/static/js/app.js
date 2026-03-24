// ============================================
// GLOBAL STATE
// ============================================

const state = {
    sessionId: generateSessionId(),
    hiddenFiles: {
        cover: null,
        secret: null
    },
    revealFiles: {
        container: null
    }
};

// ============================================
// UTILITY FUNCTIONS
// ============================================

function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function getFileExtension(filename) {
    return filename.split('.').pop().toLowerCase();
}

function isImageFile(filename) {
    const imageExts = ['png', 'jpg', 'jpeg', 'bmp'];
    return imageExts.includes(getFileExtension(filename));
}

function isVideoFile(filename) {
    const videoExts = ['mp4', 'avi', 'mov', 'mkv'];
    return videoExts.includes(getFileExtension(filename));
}

// ============================================
// UPLOAD HANDLERS
// ============================================

function setupUploadBox(boxId, inputId, callback) {
    const box = document.getElementById(boxId);
    const input = document.getElementById(inputId);

    // Click to upload
    box.addEventListener('click', () => input.click());

    // File selection
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            uploadFile(file, boxId, inputId, callback);
        }
    });

    // Drag and drop
    box.addEventListener('dragover', (e) => {
        e.preventDefault();
        box.style.borderColor = '#ec4899';
        box.style.background = 'rgba(236, 72, 153, 0.15)';
    });

    box.addEventListener('dragleave', () => {
        box.style.borderColor = '#6366f1';
        box.style.background = 'linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%)';
    });

    box.addEventListener('drop', (e) => {
        e.preventDefault();
        box.style.borderColor = '#6366f1';
        box.style.background = 'linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%)';
        
        const file = e.dataTransfer.files[0];
        if (file) {
            uploadFile(file, boxId, inputId, callback);
        }
    });
}

async function uploadFile(file, boxId, inputId, callback) {
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            showError(boxId, data.error);
            return;
        }

        // Show file info
        showFileInfo(boxId, file.name, file.size);

        // Call callback with file info
        if (callback) {
            callback(data);
        }

    } catch (error) {
        showError(boxId, 'Upload failed: ' + error.message);
    }
}

function showFileInfo(boxId, filename, size) {
    const box = document.getElementById(boxId);
    const infoDiv = box.querySelector('.file-info');
    
    if (infoDiv) {
        infoDiv.innerHTML = `
            <p><strong>✓ File uploaded:</strong></p>
            <p>${filename}</p>
            <p>Size: ${formatFileSize(size)}</p>
        `;
        infoDiv.style.display = 'block';
    }
}

function showError(boxId, message) {
    const box = document.getElementById(boxId);
    alert('Error: ' + message);
}

// ============================================
// TAB SWITCHING
// ============================================

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabId = btn.dataset.tab;

        // Update buttons
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabId).classList.add('active');
    });
});

// ============================================
// HIDE IMAGE IN IMAGE
// ============================================

setupUploadBox('cover-upload-image', 'cover-image-input', (data) => {
    state.hiddenFiles.cover = data;
    checkHideImageReady();
});

setupUploadBox('secret-upload-image', 'secret-image-input', (data) => {
    state.hiddenFiles.secret = data;
    checkHideImageReady();
});

function checkHideImageReady() {
    const btn = document.getElementById('hide-image-btn');
    btn.disabled = !(state.hiddenFiles.cover && state.hiddenFiles.secret);
}

document.getElementById('hide-image-btn').addEventListener('click', async () => {
    const shuffle = document.getElementById('shuffle-image').checked;
    await processHideImage(shuffle);
});

async function processHideImage(shuffle) {
    try {
        showProgress('hide-image');
        
        const response = await fetch('/api/hide-image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId,
                cover_path: state.hiddenFiles.cover.filepath,
                secret_path: state.hiddenFiles.secret.filepath,
                use_shuffle: shuffle
            })
        });

        if (!response.ok) {
            const error = await response.json();
            showError('hide-image', error.error);
            hideProgress('hide-image');
            return;
        }

        // Poll for completion
        await pollProcessing('hide-image', async (status) => {
            showResult('hide-image', status.filename, true);
        });

    } catch (error) {
        showError('hide-image', error.message);
        hideProgress('hide-image');
    }
}

// ============================================
// HIDE VIDEO IN VIDEO
// ============================================

setupUploadBox('cover-upload-video', 'cover-video-input', (data) => {
    state.hiddenFiles.cover = data;
    checkHideVideoReady();
});

setupUploadBox('secret-upload-video', 'secret-image-video-input', (data) => {
    state.hiddenFiles.secret = data;
    checkHideVideoReady();
});

function checkHideVideoReady() {
    const btn = document.getElementById('hide-video-btn');
    btn.disabled = !(state.hiddenFiles.cover && state.hiddenFiles.secret);
}

document.getElementById('hide-video-btn').addEventListener('click', async () => {
    const shuffle = document.getElementById('shuffle-video').checked;
    await processHideVideo(shuffle);
});

async function processHideVideo(shuffle) {
    try {
        showProgress('hide-video');
        
        const response = await fetch('/api/hide-video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId,
                cover_path: state.hiddenFiles.cover.filepath,
                secret_path: state.hiddenFiles.secret.filepath,
                use_shuffle: shuffle
            })
        });

        if (!response.ok) {
            const error = await response.json();
            showError('hide-video', error.error);
            hideProgress('hide-video');
            return;
        }

        // Poll for completion
        await pollProcessing('hide-video', async (status) => {
            showResult('hide-video', status.filename, false);
        });

    } catch (error) {
        showError('hide-video', error.message);
        hideProgress('hide-video');
    }
}

// ============================================
// REVEAL IMAGE FROM IMAGE
// ============================================

setupUploadBox('container-upload-image', 'container-image-input', (data) => {
    state.revealFiles.container = data;
    document.getElementById('reveal-image-btn').disabled = false;
});

document.getElementById('reveal-image-btn').addEventListener('click', async () => {
    const shuffle = document.getElementById('shuffle-reveal-image').checked;
    await processRevealImage(shuffle);
});

async function processRevealImage(shuffle) {
    try {
        showProgress('reveal-image');
        
        const response = await fetch('/api/reveal-image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId,
                container_path: state.revealFiles.container.filepath,
                use_shuffle: shuffle
            })
        });

        if (!response.ok) {
            const error = await response.json();
            showError('reveal-image', error.error);
            hideProgress('reveal-image');
            return;
        }

        // Poll for completion
        await pollProcessing('reveal-image', async (status) => {
            showResult('reveal-image', status.filename, true);
        });

    } catch (error) {
        showError('reveal-image', error.message);
        hideProgress('reveal-image');
    }
}

// ============================================
// REVEAL VIDEO FROM VIDEO
// ============================================

setupUploadBox('container-upload-video', 'container-video-input', (data) => {
    state.revealFiles.container = data;
    document.getElementById('reveal-video-btn').disabled = false;
});

document.getElementById('reveal-video-btn').addEventListener('click', async () => {
    const shuffle = document.getElementById('shuffle-reveal-video').checked;
    await processRevealVideo(shuffle);
});

async function processRevealVideo(shuffle) {
    try {
        showProgress('reveal-video');
        
        const response = await fetch('/api/reveal-video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId,
                container_path: state.revealFiles.container.filepath,
                use_shuffle: shuffle
            })
        });

        if (!response.ok) {
            const error = await response.json();
            showError('reveal-video', error.error);
            hideProgress('reveal-video');
            return;
        }

        // Poll for completion
        await pollProcessing('reveal-video', async (status) => {
            showResult('reveal-video', status.filename, false);
        });

    } catch (error) {
        showError('reveal-video', error.message);
        hideProgress('reveal-video');
    }
}

// ============================================
// PROGRESS & STATUS
// ============================================

function showProgress(type) {
    document.getElementById(`${type}-progress`).style.display = 'block';
    document.getElementById(`${type}-result`).style.display = 'none';
    document.getElementById(`${type}-error`).style.display = 'none';
    document.getElementById(`${type}-btn`).disabled = true;
}

function hideProgress(type) {
    document.getElementById(`${type}-progress`).style.display = 'none';
}

async function pollProcessing(type, onComplete) {
    const maxAttempts = 600; // 10 minutes with 1s intervals
    let attempts = 0;
    let finalStatus = null;

    while (attempts < maxAttempts) {
        try {
            const response = await fetch(`/api/status/${state.sessionId}`);
            const status = await response.json();
            finalStatus = status;

            // Update progress bar
            const progressFill = document.getElementById(`${type}-progress-fill`);
            const progressPercent = document.getElementById(`${type}-percent`);
            
            if (progressFill && progressPercent) {
                progressFill.style.width = status.progress + '%';
                progressPercent.textContent = status.progress + '%';
            }

            // Update status text
            const statusText = document.getElementById(`${type}-status`);
            if (statusText) {
                statusText.textContent = capitalizeStatus(status.status);
            }

            if (status.status === 'completed') {
                hideProgress(type);
                await onComplete(status);
                return;
            }

            if (status.status === 'error') {
                hideProgress(type);
                document.getElementById(`${type}-error`).style.display = 'block';
                document.getElementById(`${type}-error-msg`).textContent = status.error;
                document.getElementById(`${type}-btn`).disabled = false;
                return;
            }

            // Wait before next poll
            await new Promise(resolve => setTimeout(resolve, 1000));
            attempts++;

        } catch (error) {
            console.error('Status poll error:', error);
            await new Promise(resolve => setTimeout(resolve, 1000));
            attempts++;
        }
    }

    // Timeout
    hideProgress(type);
    document.getElementById(`${type}-error`).style.display = 'block';
    document.getElementById(`${type}-error-msg`).textContent = 'Processing timeout. Please try again.';
    document.getElementById(`${type}-btn`).disabled = false;
}

function capitalizeStatus(status) {
    const statusMap = {
        'loading_images': 'Loading images...',
        'loading': 'Loading files...',
        'shuffling': 'Applying security enhancement...',
        'encoding': 'Encoding secret data...',
        'encoding_frames': 'Encoding video frames...',
        'saving': 'Saving results...',
        'processing_video': 'Processing video...',
        'decoding': 'Decoding hidden data...',
        'loading_video': 'Loading video...',
        'completed': 'Completed!'
    };
    return statusMap[status] || status;
}

// ============================================
// RESULT DISPLAY
// ============================================

function showResult(type, filename, isImage) {
    const resultSection = document.getElementById(`${type}-result`);
    resultSection.style.display = 'block';

    if (isImage && filename) {
        const previewImg = document.getElementById(`${type}-preview`);
        previewImg.src = `/api/preview/${filename}`;
    }

    // Setup download button
    if (filename) {
        const downloadBtn = document.getElementById(`${type}-download`);
        downloadBtn.onclick = () => {
            window.location.href = `/api/download/${filename}`;
        };
    }

    // Setup reset button
    const resetBtn = document.getElementById(`${type}-reset`);
    resetBtn.onclick = () => {
        resetTab(type);
    };
}

function resetTab(type) {
    // Hide result section
    document.getElementById(`${type}-result`).style.display = 'none';
    document.getElementById(`${type}-error`).style.display = 'none';
    document.getElementById(`${type}-progress`).style.display = 'none';

    // Reset progress bar
    const progressFill = document.getElementById(`${type}-progress-fill`);
    if (progressFill) {
        progressFill.style.width = '0%';
    }

    const progressPercent = document.getElementById(`${type}-percent`);
    if (progressPercent) {
        progressPercent.textContent = '0%';
    }

    // Re-enable button
    const btn = document.getElementById(`${type}-btn`);
    if (btn) {
        btn.disabled = false;
    }

    // Clear file uploads based on type
    if (type.includes('hide')) {
        clearFileSection(`cover-image-input`, `cover-${type.includes('video') ? 'video' : 'image'}-info`);
        clearFileSection(`secret-image-input`, `secret-image-info`);
        clearFileSection(`secret-image-video-input`, `secret-image-video-info`);
        state.hiddenFiles = { cover: null, secret: null };
    } else {
        clearFileSection(`container-image-input`, `container-image-info`);
        clearFileSection(`container-video-input`, `container-video-info`);
        state.revealFiles = { container: null };
    }

    // Generate new session ID
    state.sessionId = generateSessionId();
}

function clearFileSection(inputId, infoId) {
    const input = document.getElementById(inputId);
    if (input) {
        input.value = '';
    }
    const info = document.getElementById(infoId);
    if (info) {
        info.style.display = 'none';
    }
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('✓ StegoAI Interface loaded');
    checkHideImageReady();
});
