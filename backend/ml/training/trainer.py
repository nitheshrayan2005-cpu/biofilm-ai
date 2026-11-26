"""
BiofilmAI ML — Trainer
=======================
Training pipeline for the multimodal model.

This module provides:
- Data loading (expects a labeled dataset)
- Training loop
- Validation loop
- Early stopping
- Checkpointing

No training is performed until real labelled data is provided.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, Tuple

import torch
import torch.nn as nn
import torch.optim as optim

from ..config import TrainingConfig, get_training_config
from ..model import MultimodalModel


class Trainer:
    """
    Training pipeline for the multimodal model.
    
    Usage:
        trainer = Trainer(model, config)
        trainer.train(train_loader, val_loader)
    
    Before training:
    - A labeled dataset is required
    - Data must be split into train/validation/test sets
    - Each sample must have: (microscopy, spectroscopy, genomics, clinical, label)
    
    After training:
    - Weights are saved to checkpoint_dir
    - Model is ready for inference
    """
    
    def __init__(
        self,
        model: MultimodalModel,
        config: Optional[TrainingConfig] = None,
        device: str = "cpu",
    ):
        self.model = model
        self.config = config or get_training_config()
        self.device = device
        self.criterion = nn.BCELoss()
        self.optimizer = optim.AdamW(
            model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=self.config.epochs,
        )
        self.best_val_loss = float("inf")
        self.patience_counter = 0
    
    def train(
        self,
        train_loader,
        val_loader,
    ) -> Dict[str, Any]:
        """
        Run the training loop.
        
        Args:
            train_loader: DataLoader for training data
            val_loader: DataLoader for validation data
        
        Returns:
            Dict with training history (losses, metrics)
        """
        print(f"[BiofilmAI] Starting training for {self.config.epochs} epochs")
        print(f"[BiofilmAI] Batch size: {self.config.batch_size}")
        print(f"[BiofilmAI] Learning rate: {self.config.learning_rate}")
        
        history = {"train_loss": [], "val_loss": [], "val_metrics": []}
        
        for epoch in range(self.config.epochs):
            # Train
            train_loss = self._train_epoch(train_loader)
            history["train_loss"].append(train_loss)
            
            # Validate
            val_loss, val_metrics = self._validate_epoch(val_loader)
            history["val_loss"].append(val_loss)
            history["val_metrics"].append(val_metrics)
            
            # Early stopping
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.patience_counter = 0
                self._save_checkpoint(epoch)
            else:
                self.patience_counter += 1
                if self.patience_counter >= self.config.early_stopping_patience:
                    print(f"[BiofilmAI] Early stopping at epoch {epoch}")
                    break
            
            # Log
            if epoch % self.config.log_interval == 0:
                print(f"Epoch {epoch}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")
        
        return history
    
    def _train_epoch(self, train_loader) -> float:
        """Train one epoch."""
        self.model.train()
        total_loss = 0
        num_batches = 0
        
        for batch in train_loader:
            self.optimizer.zero_grad()
            output = self.model(**batch)
            loss = self.criterion(output["prediction"], batch["labels"].float())
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
            self.optimizer.step()
            total_loss += loss.item()
            num_batches += 1
        
        self.scheduler.step()
        return total_loss / max(num_batches, 1)
    
    def _validate_epoch(self, val_loader) -> Tuple[float, Dict]:
        """Validate one epoch."""
        self.model.eval()
        total_loss = 0
        num_batches = 0
        metrics = {}
        
        with torch.no_grad():
            for batch in val_loader:
                output = self.model(**batch)
                loss = self.criterion(output["prediction"], batch["labels"].float())
                total_loss += loss.item()
                num_batches += 1
        
        return total_loss / max(num_batches, 1), metrics
    
    def _save_checkpoint(self, epoch: int):
        """Save model checkpoint."""
        import os
        os.makedirs(self.config.checkpoint_dir, exist_ok=True)
        path = os.path.join(self.config.checkpoint_dir, f"model_epoch_{epoch}.pt")
        torch.save(self.model.state_dict(), path)
        print(f"[BiofilmAI] Checkpoint saved: {path}")