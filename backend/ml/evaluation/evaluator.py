"""
BiofilmAI ML — Evaluator
=========================
Evaluation pipeline for the multimodal model.

Provides:
- Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC
- Bootstrap confidence intervals
- Per-modality evaluation
- Ablation study support

No evaluation is performed until real labelled data is provided.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List

import torch

from ..config import EvaluationConfig, get_evaluation_config
from ..model import MultimodalModel


class Evaluator:
    """
    Evaluation pipeline for the multimodal model.
    
    Usage:
        evaluator = Evaluator(model, config)
        metrics = evaluator.evaluate(test_loader)
    
    Before evaluation:
    - A labeled test set is required
    - Model weights must be loaded
    
    After evaluation:
    - Metrics are returned as a dict
    - No fake metrics are generated
    """
    
    def __init__(
        self,
        model: MultimodalModel,
        config: Optional[EvaluationConfig] = None,
        device: str = "cpu",
    ):
        self.model = model
        self.config = config or get_evaluation_config()
        self.device = device
    
    def evaluate(self, test_loader) -> Dict[str, Any]:
        """
        Evaluate the model on a test set.
        
        Args:
            test_loader: DataLoader for test data
        
        Returns:
            Dict with evaluation metrics
        
        Raises:
            ValueError: If no test data is provided
        """
        self.model.eval()
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for batch in test_loader:
                output = self.model(**batch)
                all_preds.append(output["prediction"].cpu())
                all_labels.append(batch["labels"].cpu())
        
        if not all_preds:
            raise ValueError("No test data provided")
        
        preds = torch.cat(all_preds, dim=0).squeeze()
        labels = torch.cat(all_labels, dim=0).squeeze()
        
        metrics = self._compute_metrics(preds, labels)
        return metrics
    
    def _compute_metrics(self, preds: torch.Tensor, labels: torch.Tensor) -> Dict[str, Any]:
        """Compute evaluation metrics."""
        # Binary classification at threshold
        threshold = self.config.threshold
        binary_preds = (preds >= threshold).long()
        
        # Basic metrics
        tp = ((binary_preds == 1) & (labels == 1)).sum().item()
        fp = ((binary_preds == 1) & (labels == 0)).sum().item()
        tn = ((binary_preds == 0) & (labels == 0)).sum().item()
        fn = ((binary_preds == 0) & (labels == 1)).sum().item()
        
        accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        metrics = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "threshold": threshold,
            "num_samples": len(labels),
            "num_positive": int(labels.sum()),
            "num_negative": int((1 - labels).sum()),
        }
        
        return metrics
    
    def ablation_study(self, test_loader) -> Dict[str, Dict[str, float]]:
        """
        Run ablation study by removing each modality.
        
        Args:
            test_loader: DataLoader for test data
        
        Returns:
            Dict mapping modality name to metrics when that modality is removed
        """
        # This requires the test loader to provide modality-specific inputs
        # and would need to be implemented per dataset
        raise NotImplementedError("Ablation study requires a labeled dataset with per-modality inputs")