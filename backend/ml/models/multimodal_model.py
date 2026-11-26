"""
BiofilmAI ML — Models: Multimodal Model (scaffold)
====================================================

Multimodal research architecture:

    Microscopy   → MicroscopyEncoder   → ┐
    Spectroscopy → SpectroscopyEncoder → ┤
    Genomics     → GenomicsEncoder     → ┼→ CrossAttentionFusion → Multimodal
    Clinical     → ClinicalEncoder     → ┘      Representation      → Prediction Head

STATUS: ARCHITECTURE ONLY — NOT TRAINED.

Behaviour contract:
  - Every modality is optional; explicit modality masks are required.
  - At least one modality must be present — an all-missing call FAILS clearly.
  - Shape validation is enforced per modality (wrong dimensions raise).
  - Batch dimensions must be consistent across provided modalities.
  - forward() returns model_mode="untrained_multimodal" and prediction=None.
  - predict() refuses to run (raises) — the model NEVER fabricates a
    clinical prediction.
"""

from __future__ import annotations

from typing import Dict, Optional

import torch
import torch.nn as nn

from .config import MultimodalConfig, default_config
from .microscopy_encoder import MicroscopyEncoder
from .spectroscopy_encoder import SpectroscopyEncoder
from .genomics_encoder import GenomicsEncoder
from .clinical_encoder import ClinicalEncoder
from .cross_attention_fusion import CrossAttentionFusion

# Explicit modality names (canonical order)
MODALITIES = ["microscopy", "spectroscopy", "genomics", "clinical"]

MODEL_MODE = "untrained_multimodal"


class MultimodalModel(nn.Module):
    """
    Untrained multimodal architecture scaffold.

    Args:
        config: MultimodalConfig

    Input (forward):
        microscopy:   (B, 3, 224, 224) float tensor, optional
        spectroscopy: (B, seq_len, 2) float tensor, optional
        genomics:     (B, max_seq_len) long tensor, optional
        genomics_mask:(B, max_seq_len) bool tensor, optional (with genomics)
        clinical:     (B, 32) float tensor, optional
        modalities_present: dict[str, bool] — explicit availability flags

    Returns (dict):
        unified_representation, modality_embeddings, contributions,
        cross_attention, model_mode="untrained_multimodal",
        prediction=None, modalities_present
    """

    def __init__(self, config: Optional[MultimodalConfig] = None):
        super().__init__()
        self.config = config or default_config()
        self.modalities = list(self.config.modalities)

        self.microscopy_encoder = MicroscopyEncoder()
        self.spectroscopy_encoder = SpectroscopyEncoder()
        self.genomics_encoder = GenomicsEncoder()
        self.clinical_encoder = ClinicalEncoder()
        self.fusion = CrossAttentionFusion()

        # Prediction head exists for FUTURE training but is never used
        # until the model is trained (forward returns prediction=None).
        self.prediction_head = nn.Sequential(
            nn.Linear(128, self.config.prediction_hidden_dim),
            nn.GELU(),
            nn.Linear(self.config.prediction_hidden_dim, 1),
            nn.Sigmoid(),
        )

    # ── Validation helpers ────────────────────────────────────────────────

    def _validate_presence(self, modalities_present: Optional[Dict[str, bool]]) -> Dict[str, bool]:
        """Validate the explicit modality mask and return a canonical dict."""
        if modalities_present is None:
            raise ValueError(
                "modalities_present is required. Provide an explicit dict of "
                "availability flags for each modality."
            )
        if set(modalities_present.keys()) != set(self.modalities):
            raise ValueError(
                f"modalities_present must contain exactly {self.modalities}; "
                f"got {sorted(modalities_present.keys())}"
            )
        present = {m: bool(modalities_present[m]) for m in self.modalities}
        if not any(present.values()):
            raise ValueError(
                "ALL MODALITIES MISSING — cannot run the multimodal model. "
                "At least one modality must be present."
            )
        return present

    def _validate_shapes(
        self,
        microscopy: Optional[torch.Tensor],
        spectroscopy: Optional[torch.Tensor],
        genomics: Optional[torch.Tensor],
        genomics_mask: Optional[torch.Tensor],
        clinical: Optional[torch.Tensor],
        present: Dict[str, bool],
    ) -> int:
        """Validate per-modality shapes + batch consistency. Returns batch size."""
        # Presence-flag vs tensor consistency
        if present["microscopy"] and microscopy is None:
            raise ValueError("modalities_present['microscopy']=True but microscopy tensor is None")
        if present["spectroscopy"] and spectroscopy is None:
            raise ValueError("modalities_present['spectroscopy']=True but spectroscopy tensor is None")
        if present["genomics"] and genomics is None:
            raise ValueError("modalities_present['genomics']=True but genomics tensor is None")
        if present["clinical"] and clinical is None:
            raise ValueError("modalities_present['clinical']=True but clinical tensor is None")
        for name, tensor, flag in [
            ("microscopy", microscopy, present["microscopy"]),
            ("spectroscopy", spectroscopy, present["spectroscopy"]),
            ("genomics", genomics, present["genomics"]),
            ("clinical", clinical, present["clinical"]),
        ]:
            if tensor is not None and not flag:
                raise ValueError(
                    f"{name} tensor provided but modalities_present['{name}']=False"
                )

        batch: Optional[int] = None
        cfg = self.config

        if microscopy is not None:
            if microscopy.ndim != 4:
                raise ValueError(
                    f"microscopy must be 4D (B, {cfg.image_channels}, {cfg.image_size}, "
                    f"{cfg.image_size}); got shape {tuple(microscopy.shape)}"
                )
            if microscopy.shape[1] != cfg.image_channels:
                raise ValueError(f"microscopy channels must be {cfg.image_channels}; got {microscopy.shape[1]}")
            if microscopy.shape[2] != cfg.image_size or microscopy.shape[3] != cfg.image_size:
                raise ValueError(
                    f"microscopy spatial size must be {cfg.image_size}×{cfg.image_size}; got {microscopy.shape[2:]}"
                )
            batch = microscopy.shape[0]

        if spectroscopy is not None:
            if spectroscopy.ndim != 3:
                raise ValueError(f"spectroscopy must be 3D (B, seq_len, 2); got shape {tuple(spectroscopy.shape)}")
            if spectroscopy.shape[2] != cfg.spectroscopy_input_dim:
                raise ValueError(f"spectroscopy last dim must be {cfg.spectroscopy_input_dim}; got {spectroscopy.shape[2]}")
            batch = batch or spectroscopy.shape[0]

        if genomics is not None:
            if genomics.ndim != 2:
                raise ValueError(f"genomics must be 2D (B, max_seq_len); got shape {tuple(genomics.shape)}")
            if genomics.dtype not in (torch.long, torch.int32, torch.int64):
                raise ValueError(f"genomics must be an integer token tensor; got dtype {genomics.dtype}")
            if genomics_mask is not None:
                if genomics_mask.shape != genomics.shape:
                    raise ValueError(
                        f"genomics_mask shape {tuple(genomics_mask.shape)} must match genomics {tuple(genomics.shape)}"
                    )
                if genomics_mask.dtype != torch.bool:
                    raise ValueError(f"genomics_mask must be bool; got {genomics_mask.dtype}")
            batch = batch or genomics.shape[0]

        if clinical is not None:
            if clinical.ndim != 2:
                raise ValueError(f"clinical must be 2D (B, 32); got shape {tuple(clinical.shape)}")
            if clinical.shape[1] != cfg.clinical_input_dim:
                raise ValueError(f"clinical last dim must be {cfg.clinical_input_dim}; got {clinical.shape[1]}")
            batch = batch or clinical.shape[0]

        # Batch consistency across modalities
        for name, tensor in [("microscopy", microscopy), ("spectroscopy", spectroscopy),
                             ("genomics", genomics), ("clinical", clinical)]:
            if tensor is not None and tensor.shape[0] != batch:
                raise ValueError(
                    f"Batch mismatch: {name} has batch {tensor.shape[0]} but expected {batch}"
                )

        if batch is None:
            raise ValueError("No modality tensors provided.")
        return batch

    # ── Forward ───────────────────────────────────────────────────────────

    def forward(
        self,
        microscopy: Optional[torch.Tensor] = None,
        spectroscopy: Optional[torch.Tensor] = None,
        genomics: Optional[torch.Tensor] = None,
        genomics_mask: Optional[torch.Tensor] = None,
        clinical: Optional[torch.Tensor] = None,
        modalities_present: Optional[Dict[str, bool]] = None,
    ) -> Dict:
        present = self._validate_presence(modalities_present)
        batch = self._validate_shapes(
            microscopy, spectroscopy, genomics, genomics_mask, clinical, present
        )

        embeddings: Dict[str, torch.Tensor] = {}
        if present["microscopy"]:
            embeddings["microscopy"] = self.microscopy_encoder(microscopy)
        if present["spectroscopy"]:
            embeddings["spectroscopy"] = self.spectroscopy_encoder(spectroscopy)
        if present["genomics"]:
            embeddings["genomics"] = self.genomics_encoder(genomics, genomics_mask)
        if present["clinical"]:
            embeddings["clinical"] = self.clinical_encoder(clinical)

        # Fusion receives only the present modalities (explicit mask).
        mask_tensor = {m: torch.tensor([present[m]], dtype=torch.bool) for m in self.modalities}
        unified, attn, contributions = self.fusion(embeddings, mask_tensor)

        return {
            "unified_representation": unified,          # (B, 128)
            "modality_embeddings": {k: v.detach() for k, v in embeddings.items()},
            "contributions": contributions,
            "cross_attention": attn,
            "modalities_present": present,
            "batch_size": batch,
            # Honest untrained state — never a real prediction:
            "prediction": None,
            "risk_category": None,
            "model_mode": MODEL_MODE,
        }

    def predict(self, *args, **kwargs) -> Dict:
        """Refuse to predict — the multimodal model is NOT trained."""
        raise RuntimeError(
            "Multimodal model is UNTRAINED (architecture scaffold only). "
            "It cannot produce a prediction. A valid paired four-modality "
            "dataset and training are required first."
        )
