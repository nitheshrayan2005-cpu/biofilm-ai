"""
BiofilmAI Backend — Model Manager
===================================
Central manager for the ML model lifecycle.

Provides:
- Loading trained weights
- Checking if real model is available
- Running inference (real or demo)
- Clean fallback to demo mode
"""

from __future__ import annotations

import os
import logging
from typing import Optional, Dict, Any

from config import settings

logger = logging.getLogger("biofilm-ai")


class ModelManager:
    """
    Manages the ML model lifecycle.
    
    The model manager:
    1. Checks if trained weights exist at startup
    2. Loads the model if weights are found
    3. Falls back to demo mode if no weights
    4. Provides inference via a unified interface
    """
    
    def __init__(self):
        self._predictor = None
        self._is_demo = True
        self._model_info = {
            "loaded": False,
            "weight_path": None,
            "model_mode": "demo",
        }
    
    def initialize(self):
        """Initialize the model manager. Called at server startup."""
        weight_path = settings.MODEL_WEIGHTS_PATH
        
        if os.path.exists(weight_path):
            logger.info(f"Found model weights at {weight_path}")
            self._try_load_model(weight_path)
        else:
            logger.info(f"No weights found at {weight_path}. Running in DEMO MODE.")
            self._is_demo = True
            self._model_info["model_mode"] = "demo"
    
    def _try_load_model(self, weight_path: str):
        """Try to load the model from weights."""
        try:
            from ml.inference import MultimodalPredictor
            from ml.model_config import default_config

            config = default_config()
            config.weights_path = weight_path
            config.device = settings.MODEL_DEVICE

            self._predictor = MultimodalPredictor(config, device=settings.MODEL_DEVICE)
            if self._predictor.load_model(weight_path):
                self._is_demo = False
                self._model_info = {
                    "loaded": True,
                    "weight_path": weight_path,
                    "model_mode": "model",
                }
                logger.info(f"Model loaded successfully from {weight_path}")
            else:
                self._is_demo = True
                self._model_info["model_mode"] = "demo"
                logger.warning(f"Failed to load model from {weight_path}")
        except ImportError as e:
            logger.warning(f"Cannot load ML modules: {e}. Running in DEMO MODE.")
            self._is_demo = True
            self._model_info["model_mode"] = "demo"
        except Exception as e:
            logger.error(f"Error loading model: {e}. Running in DEMO MODE.")
            self._is_demo = True
            self._model_info["model_mode"] = "demo"
    
    @property
    def is_demo(self) -> bool:
        """Whether the system is in demo mode."""
        return self._is_demo
    
    @property
    def model_mode(self) -> str:
        """Current model mode string."""
        return self._model_info.get("model_mode", "demo")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model state."""
        return dict(self._model_info)
    
    def run_inference(
        self,
        sample_info: dict,
        clinical_data: dict,
        microscopy_bytes: Optional[bytes] = None,
        spectroscopy_bytes: Optional[bytes] = None,
        genomics_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Run inference — real if model is loaded, otherwise returns empty.
        
        Returns:
            Dict with 'prediction' key (None if demo) and 'model_mode' key.
        """
        if not self._is_demo and self._predictor is not None:
            try:
                return self._predictor.predict(
                    sample_info=sample_info,
                    clinical_data=clinical_data,
                    microscopy_bytes=microscopy_bytes,
                    spectroscopy_bytes=spectroscopy_bytes,
                    genomics_bytes=genomics_bytes,
                )
            except Exception as e:
                logger.error(f"Inference failed: {e}")
                return {
                    "prediction": None,
                    "risk_category": None,
                    "contributions": {},
                    "cross_attention": None,
                    "model_mode": "error",
                }
        
        return {
            "prediction": None,
            "risk_category": None,
            "contributions": {},
            "cross_attention": None,
            "model_mode": "unavailable",
        }


# Global singleton
model_manager = ModelManager()