"""
Train lightweight autoencoders for video steganography
Optimized for GTX 1650 Ti with minimal memory footprint
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import os

# GPU memory optimization
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(f"GPU config failed: {e}")

# Create synthetic training data (224x224 RGB)
print("Generating synthetic training data...")
X_train = np.random.randint(0, 256, (100, 224, 224, 3), dtype=np.uint8).astype(np.float32) / 255.0
print(f"Training data shape: {X_train.shape}")

# Simple but effective autoencoder architecture
def create_video_autoencoder():
    """Create lightweight autoencoder for video frames"""
    
    inputs = keras.Input(shape=(224, 224, 3))
    
    # Encoder
    x = layers.Conv2D(16, 3, padding='same', activation='relu')(inputs)
    x = layers.MaxPooling2D(2)(x)  # 112x112
    x = layers.Conv2D(32, 3, padding='same', activation='relu')(x)
    x = layers.MaxPooling2D(2)(x)  # 56x56
    x = layers.Conv2D(64, 3, padding='same', activation='relu')(x)
    encoded = layers.MaxPooling2D(2)(x)  # 28x28
    
    # Decoder
    x = layers.UpSampling2D(2)(encoded)  # 56x56
    x = layers.Conv2D(64, 3, padding='same', activation='relu')(x)
    x = layers.UpSampling2D(2)(x)  # 112x112
    x = layers.Conv2D(32, 3, padding='same', activation='relu')(x)
    x = layers.UpSampling2D(2)(x)  # 224x224
    x = layers.Conv2D(16, 3, padding='same', activation='relu')(x)
    decoded = layers.Conv2D(3, 3, padding='same', activation='sigmoid')(x)
    
    autoencoder = keras.Model(inputs, decoded)
    return autoencoder

print("\nBuilding autoencoders...")
hide_model = create_video_autoencoder()
reveal_model = create_video_autoencoder()

print("Compiling models...")
hide_model.compile(optimizer='adam', loss='mse')
reveal_model.compile(optimizer='adam', loss='mse')

print("\nTraining hide model...")
hide_model.fit(X_train, X_train, epochs=5, batch_size=4, verbose=1)

print("\nTraining reveal model...")
reveal_model.fit(X_train, X_train, epochs=5, batch_size=4, verbose=1)

# Save models
print("\nSaving models...")
os.makedirs('models', exist_ok=True)

# For video: save as separate models
hide_model.save('models/hide_video.h5')
reveal_model.save('models/reveal_video.h5')

print("✓ Models saved!")
print("  - models/hide_video.h5")
print("  - models/reveal_video.h5")
print("\nTraining complete!")
