"""Unit tests for custom PyTorch Transformer Encoder architecture."""
import pytest
import torch
import torch.nn as nn
from src.model.transformer import PhishSenseTransformer, get_model_summary


def test_transformer_forward_and_backward():
    vocab_size = 500
    batch_size = 4
    seq_len = 32
    d_model = 128

    model = PhishSenseTransformer(
        vocab_size=vocab_size,
        d_model=d_model,
        nhead=4,
        dim_feedforward=256,
        num_layers=2,
        dropout=0.1,
        num_classes=2,
        pad_idx=0,
    )

    # Synthetic batch
    input_ids = torch.randint(1, vocab_size, (batch_size, seq_len))
    # Add padding to last tokens
    input_ids[:, -5:] = 0
    attention_mask = (input_ids != 0).long()
    labels = torch.tensor([0, 1, 0, 1], dtype=torch.long)

    # 1. Forward pass
    logits = model(input_ids, attention_mask)
    assert logits.shape == (batch_size, 2)
    assert torch.isfinite(logits).all(), "Logits must be finite (no NaNs or Infs)"

    # 2. Loss computation
    criterion = nn.CrossEntropyLoss()
    loss = criterion(logits, labels)
    assert torch.isfinite(loss), "Loss must be finite"

    # 3. Backward pass
    model.zero_grad()
    loss.backward()

    # 4. Check non-zero finite gradients on trainable parameters
    grad_found = False
    for name, param in model.named_parameters():
        if param.requires_grad:
            assert param.grad is not None, f"Gradient missing for {name}"
            assert torch.isfinite(param.grad).all(), f"Gradient not finite for {name}"
            if param.grad.abs().sum() > 0:
                grad_found = True
    assert grad_found, "At least one parameter must have non-zero gradient"


def test_model_summary():
    model = PhishSenseTransformer(vocab_size=1000, d_model=128)
    summary = get_model_summary(model)
    assert "PhishSense Custom PyTorch Transformer Architecture" in summary
    assert "Total Parameters:" in summary
    assert "Trainable Parameters:" in summary
