"""
BiofilmAI ML — Clinical Preprocessing
=======================================
Preprocessing pipeline for clinical data.

Steps:
1. Extract features from clinical data dict
2. Encode categorical variables
3. Normalize numeric values
4. Create feature vector

Output: (1, 32) tensor
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import torch


def preprocess_clinical(clinical_data: dict, device: str = "cpu") -> Optional[torch.Tensor]:
    """
    Preprocess clinical data.
    
    Args:
        clinical_data: Dict with clinical fields
        device: Target device
    
    Returns:
        tensor: (1, 32) clinical feature vector or None if failed
    """
    try:
        features = np.zeros(32, dtype=np.float32)
        
        # Infection context (one-hot)
        ctx = clinical_data.get("infectionContext", "")
        ctx_map = {"chronic-wound": 0, "orthopedic-implant": 1, "catheter": 2,
                   "post-surgical": 3, "burn": 4, "periodontal": 5}
        if ctx in ctx_map:
            features[ctx_map[ctx]] = 1
        
        # Implant
        if clinical_data.get("implantPresent", False):
            features[6] = 1
        
        # Chronicity (normalized)
        features[7] = min(clinical_data.get("chronicityDays", 0) / 365.0, 1.0)
        
        # Sample site
        site = clinical_data.get("sampleSite", "")
        site_map = {"Abdomen": 8, "Knee (prosthetic)": 9, "Lower leg": 10,
                    "Forearm": 11, "Hip": 12, "Mandible": 13}
        if site in site_map:
            features[site_map[site]] = 1
        
        # Previous treatment
        treat = clinical_data.get("previousTreatment", "")
        treat_map = {"none": 14, "antibiotics": 15, "surgical-debridement": 16, "combination": 17}
        if treat in treat_map:
            features[treat_map[treat]] = 1
        
        # Previous culture
        culture = clinical_data.get("previousCulture", "")
        culture_map = {"negative": 18, "positive-mixed": 19, "positive-pure": 20, "unknown": 21}
        if culture in culture_map:
            features[culture_map[culture]] = 1
        
        # Sample type
        stype = clinical_data.get("sampleType", "")
        stype_map = {"Wound swab": 22, "Implant sonicate": 23, "Tissue biopsy": 24,
                     "Sputum": 25, "Blood culture": 26, "Urine sample": 27}
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
        
        # Bias
        features[31] = 1.0
        
        return torch.tensor(features, dtype=torch.float32, device=device).unsqueeze(0)
    except Exception:
        return None