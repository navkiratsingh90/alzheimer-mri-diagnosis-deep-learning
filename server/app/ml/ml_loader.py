import tensorflow as tf
import numpy as np
from PIL import Image
import os
from typing import Tuple

from app.core.config import settings

# ── Constants matching the notebook ───────────────────────
IMG_SIZE = (128, 128)
CLASSES = [
    "Non Demented",
    "Very mild Dementia",
    "Mild Dementia",
    "Moderate Dementia"
]

_model = None


def load_model():
    global _model
    if _model is None:
        model_path = settings.MODEL_PATH
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
        try:
            _model = tf.keras.models.load_model(model_path)
            # Warm-up with correct input shape
            dummy = np.random.rand(1, 128, 128, 3).astype(np.float32)
            _model.predict(dummy, verbose=0)
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")
    return _model


def preprocess_image(image_path: str) -> np.ndarray:
    try:
        img = Image.open(image_path).convert("RGB")
        img = img.resize(IMG_SIZE, Image.LANCZOS)
        arr = np.array(img) / 255.0
        arr = np.expand_dims(arr, axis=0)
        return arr.astype(np.float32)
    except Exception as e:
        raise ValueError(f"Image preprocessing failed: {str(e)}")


def predict_image(image_path: str) -> Tuple[str, float]:
    model = load_model()
    batch = preprocess_image(image_path)
    preds = model.predict(batch, verbose=0)[0]
    idx = int(np.argmax(preds))
    confidence = float(np.max(preds))
    return CLASSES[idx], confidence