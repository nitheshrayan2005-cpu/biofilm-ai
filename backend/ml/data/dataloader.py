"""
BiofilmAI Data — DataLoader Factory
=====================================

Creates PyTorch DataLoaders for the BiofilmDataset.
Handles batching, shuffling, and multiprocessing.
"""

from __future__ import annotations

from typing import Dict, Optional

import torch
from torch.utils.data import DataLoader

from .dataset import BiofilmDataset
from .schema import DatasetSpec


def get_dataloaders(
    dataset_root: str,
    spec: Optional[DatasetSpec] = None,
    batch_size: int = 32,
    num_workers: int = 0,
    pin_memory: bool = False,
    data_available: bool = False,
) -> Dict[str, Optional[DataLoader]]:
    """
    Create DataLoaders for train/val/test splits.

    Arguments:
        dataset_root: Path to the dataset directory.
        spec: DatasetSpec instance.
        batch_size: Samples per batch.
        num_workers: Data loading workers (0 = main process).
        pin_memory: Use pinned memory (set True for GPU).
        data_available: If False, returns empty loaders
                        and prints the "NO DATA" message.

    Returns:
        {"train": DataLoader or None, "val": DataLoader or None,
         "test": DataLoader or None, "full": DataLoader or None}
    """
    if not data_available:
        print("=" * 70)
        print("NO REAL DATASET AVAILABLE — MODEL REMAINS IN DEMO MODE.")
        print("=" * 70)
        return {"train": None, "val": None, "test": None, "full": None}

    spec = spec or DatasetSpec(dataset_root=dataset_root)

    loaders = {}

    for split_name in ["train", "val", "test"]:
        dataset = BiofilmDataset(
            spec=spec,
            split=split_name,
            demo_mode=False,
            data_available=data_available,
        )

        if len(dataset) == 0:
            loaders[split_name] = None
            continue

        shuffle = split_name == "train"
        loaders[split_name] = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            pin_memory=pin_memory,
            collate_fn=_collate_multimodal,
        )

    # Full dataset loader
    full_dataset = BiofilmDataset(
        spec=spec,
        split=None,
        demo_mode=False,
        data_available=data_available,
    )
    if len(full_dataset) > 0:
        loaders["full"] = DataLoader(
            full_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=pin_memory,
            collate_fn=_collate_multimodal,
        )
    else:
        loaders["full"] = None

    return loaders


def _collate_multimodal(batch) -> Dict:
    """
    Collate a batch of multimodal samples into batched tensors.

    Handles missing modalities by creating zero tensors where needed
    and passing along modality masks.
    """
    collated = {}
    modality_keys = ["microscopy", "spectroscopy", "genomics", "clinical"]

    for key in modality_keys:
        tensors = [item.get(key) for item in batch]
        present = [t is not None for t in tensors]
        if any(present):
            # Pad missing with zeros
            valid_tensors = [t for t in tensors if t is not None]
            shape = valid_tensors[0].shape
            device = valid_tensors[0].device
            batched = torch.stack(
                [
                    tensors[i] if tensors[i] is not None
                    else torch.zeros(shape, dtype=next((t.dtype for t in valid_tensors), torch.float32))
                    for i in range(len(batch))
                ]
            )
            collated[key] = batched
            collated[f"{key}_mask"] = torch.tensor(present, dtype=torch.bool)
        else:
            collated[key] = None
            collated[f"{key}_mask"] = torch.zeros(len(batch), dtype=torch.bool)

    # Labels
    labels = [item.get("labels") for item in batch]
    if any(l is not None for l in labels):
        collated["labels"] = torch.stack([
            l if l is not None else torch.tensor([-1.0])
            for l in labels
        ]).squeeze(-1)
    else:
        collated["labels"] = None

    # Modality mask
    collated["modality_mask"] = {}
    for key in modality_keys:
        collated["modality_mask"][key] = collated.get(f"{key}_mask", torch.zeros(len(batch), dtype=torch.bool))

    # Sample IDs
    collated["sample_ids"] = [item.get("sample_id") for item in batch]

    return collated