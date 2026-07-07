import tensorflow as tf
import numpy as np
from PIL import Image
import os
from typing import Tuple

from app.core.config import settings

# ── Constants ───────────────────────────────────────────────
IMG_SIZE = (224, 224)          # MobileNetV2 expected size
CLASSES = ["NonDemented", "VeryMild", "Mild", "Moderate"]

_model = None


def load_model():
    """
    Lazy-load the TensorFlow model from the saved .h5 file.
    """
    global _model
    if _model is None:
        model_path = settings.MODEL_PATH
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
        try:
            _model = tf.keras.models.load_model(model_path)
            # Warm up the model (optional – ensures it's ready)
            dummy_input = np.random.rand(1, 224, 224, 3).astype(np.float32)
            _model.predict(dummy_input, verbose=0)
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")
    return _model


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Load an image from disk, resize to 224x224, and normalize to [0,1].
    Returns a batch-ready numpy array of shape (1, 224, 224, 3).
    """
    try:
        img = Image.open(image_path).convert("RGB")
        img = img.resize(IMG_SIZE, Image.LANCZOS)
        img_array = np.array(img) / 255.0   # normalize
        img_array = np.expand_dims(img_array, axis=0)  # add batch dimension
        return img_array.astype(np.float32)
    except Exception as e:
        raise ValueError(f"Image preprocessing failed: {str(e)}")


def predict_image(image_path: str) -> Tuple[str, float]:
    """
    Load the model, preprocess the image, and return (class_label, confidence).
    """
    model = load_model()
    img_batch = preprocess_image(image_path)
    predictions = model.predict(img_batch, verbose=0)[0]  # shape (4,)
    idx = int(np.argmax(predictions))
    confidence = float(np.max(predictions))
    return CLASSES[idx], confidence