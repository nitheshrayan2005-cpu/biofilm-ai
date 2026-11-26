"""
BiofilmAI ML — Clinical Encoder
================================
Encoder for structured clinical/sample metadata.

Architecture:
  Input Features (32-dim) → MLP → Modality Embedding

The clinical encoder processes structured tabular data.
"""

from __future__ import annotations

from typing import Optional, Tuple

import torch
import torch.nn as nn

from ..config import ClinicalEncoderConfig


# Clinical feature names and indices
CLINICAL_FEATURES = [
    "infection_context_chronic_wound",
    "infection_context_orthopedic_implant",
    "infection_context_catheter",
    "infection_context_post_surgical",
    "infection_context_burn",
    "infection_context_periodontal",
    "implant_present",
    "chronicity_days_normalized",
    "sample_site_abdomen",
    "sample_site_knee",
    "sample_site_lower_leg",
    "sample_site_forearm",
    "sample_site_hip",
    "sample_site_mandible",
    "prev_treatment_none",
    "prev_treatment_antibiotics",
    "prev_treatment_surgical",
    "prev_treatment_combination",
    "prev_culture_negative",
    "prev_culture_positive_mixed",
    "prev_culture_positive_pure",
    "prev_culture_unknown",
    "sample_type_wound_swab",
    "sample_type_implant_sonicate",
    "sample_type_tissue_biopsy",
    "sample_type_sputum",
    "sample_type_blood_culture",
    "sample_type_urine",
    "wound_implant_present",
    "has_notes",
    "has_collection_date",
    "bias",
]
NUM_CLINICAL_FEATURES = len(CLINICAL_FEATURES)


class ClinicalEncoder(nn.Module):
    """
    MLP-based encoder for clinical data.
    
    Args:
        config: ClinicalEncoderConfig
    
    Input:
        x: (B, input_dim) clinical features vector
    
    Output:
        embedding: (B, hidden_dim) modality representation
    """
    
    def __init__(self, config: Optional[ClinicalEncoderConfig] = None):
        super().__init__()
        self.config = config or ClinicalEncoderConfig()
        self.net = nn.Sequential(
            nn.Linear(self.config.input_dim, self.config.hidden_dim),
            nn.GELU(),
            nn.Dropout(self.config.dropout),
            nn.Linear(self.config.hidden_dim, self.config.hidden_dim),
            nn.GELU(),
            nn.Dropout(self.config.dropout),
            nn.Linear(self.config.hidden_dim, self.config.hidden_dim),
        )
        self.norm = nn.LayerNorm(self.config.hidden_dim)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, None]:
        """
        Args:
            x: (B, input_dim) clinical feature vector
        
        Returns:
            embedding: (B, hidden_dim)
            attention_weights: None (clinical has no attention)
        """
        embedding = self.norm(self.net(x))
        return embedding, None
    
    def encode_clinical(self, clinical_data: dict, device: str = "cpu") -> Tuple[torch.Tensor, None]:
        """
        Encode raw clinical data dict into a modality embedding.
        
        Args:
            clinical_data: Dict with clinical fields
            device: Target device
        
        Returns:
            embedding: (1, hidden_dim)
            attention_weights: None
        """
        import numpy as np
        
        features = np.zeros(self.config.input_dim, dtype=np.float32)
        
        # Infection context
        ctx = clinical_data.get("infectionContext", "")
        if "chronic-wound" in ctx:
            features[0] = 1
        elif "orthopedic-implant" in ctx:
            features[1] = 1
        elif "catheter" in ctx:
            features[2] = 1
        elif "post-surgical" in ctx:
            features[3] = 1
        elif "burn" in ctx:
            features[4] = 1
        elif "periodontal" in ctx:
            features[5] = 1
        
        # Implant
        if clinical_data.get("implantPresent", False):
            features[6] = 1
        
        # Chronicity (normalized to 0-1)
        features[7] = min(clinical_data.get("chronicityDays", 0) / 365.0, 1.0)
        
        # Sample site
        site = clinical_data.get("sampleSite", "")
        site_map = {
            "Abdomen": 8, "Knee (prosthetic)": 9, "Lower leg": 10,
            "Forearm": 11, "Hip": 12, "Mandible": 13,
        }
        if site in site_map:
            features[site_map[site]] = 1
        
        # Previous treatment
        treat = clinical_data.get("previousTreatment", "")
        treat_map = {"none": 14, "antibiotics": 15, "surgical-debridement": 16, "combination": 17}
        if treat in treat_map:
            features[treat_map[treat]] = 1
        
        # Previous culture
        culture = clinical_data.get("previousCulture", "")
        culture_map = {
            "negative": 18, "positive-mixed": 19,
            "positive-pure": 20, "unknown": 21,
        }
        if culture in culture_map:
            features[culture_map[culture]] = 1
        
        # Sample type
        stype = clinical_data.get("sampleType", "")
        stype_map = {
            "Wound swab": 22, "Implant sonicate": 23, "Tissue biopsy": 24,
            "Sputum": 25, "Blood culture": 26, "Urine sample": 27,
        }
        if stype in stype_map:
            features[stype_map[stype]] = 1
        
        # Wound/implant context
        if clinical_data.get("woundOrImplant", ""):
            features[28] = 1
        
        # Has notes
        if clinical_data.get("notes", "") or clinical_data.get("additionalNotes", ""):
            features[29] = 1
        
        # Has collection date
        if clinical_data.get("collectionDate", ""):
            features[30] = 1
        
        # Bias term
        features[31] = 1.0
        
        x = torch.tensor(features, dtype=torch.float32, device=device).unsqueeze(0)
        
        with torch.no_grad():
            embedding, _ = self.forward(x)
        
        return embedding, None