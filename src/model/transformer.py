"""PyTorch Transformer from Scratch for Phishing Email Detection.

Architecture:
- Token Embedding + Positional Encoding (learned or sinusoidal)
- 2 Transformer Encoder Layers (d_model=128, nhead=4, dim_feedforward=256, dropout=0.2)
- Masked Mean Pooling across non-pad tokens
- Classification Head (Linear d_model -> 2 logits)
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 512, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [batch_size, seq_len, d_model]
        seq_len = x.size(1)
        x = x + self.pe[:, :seq_len]
        return self.dropout(x)


class PhishSenseTransformer(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        d_model: int = 128,
        nhead: int = 4,
        dim_feedforward: int = 256,
        num_layers: int = 2,
        dropout: float = 0.2,
        num_classes: int = 2,
        pad_idx: int = 0,
        max_len: int = 384,
    ):
        super().__init__()
        self.d_model = d_model
        self.pad_idx = pad_idx
        self.num_classes = num_classes

        # 1. Token Embeddings + Positional Encoding
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=pad_idx)
        self.pos_encoder = PositionalEncoding(d_model, max_len=max_len, dropout=dropout)

        # 2. Transformer Encoder Layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
        )

        # 3. Layer Normalization
        self.layer_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

        # 4. Classification Head
        self.classifier = nn.Linear(d_model, num_classes)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        initrange = 0.02
        nn.init.uniform_(self.embedding.weight, -initrange, initrange)
        if self.embedding.padding_idx is not None:
            with torch.no_grad():
                self.embedding.weight[self.embedding.padding_idx].fill_(0)
        nn.init.xavier_uniform_(self.classifier.weight)
        if self.classifier.bias is not None:
            nn.init.zeros_(self.classifier.bias)

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor = None
    ) -> torch.Tensor:
        """Forward pass.
        
        Args:
            input_ids: [batch_size, seq_len] tensor of token IDs.
            attention_mask: [batch_size, seq_len] tensor with 1 for valid tokens, 0 for pad.
        
        Returns:
            logits: [batch_size, num_classes] raw class logits.
        """
        batch_size, seq_len = input_ids.shape

        # Token embeddings scaled by sqrt(d_model)
        x = self.embedding(input_ids) * math.sqrt(self.d_model)
        x = self.pos_encoder(x)

        # Key padding mask for PyTorch Transformer: True where key is to be ignored (pad)
        if attention_mask is not None:
            # PyTorch expects True for pad tokens to be masked out
            key_padding_mask = (attention_mask == 0)
        else:
            key_padding_mask = (input_ids == self.pad_idx)

        # Transformer Encoder
        encoded = self.transformer_encoder(x, src_key_padding_mask=key_padding_mask)
        encoded = self.layer_norm(encoded)

        # Masked Mean Pooling: average representations of valid tokens only
        if attention_mask is not None:
            mask_expanded = attention_mask.unsqueeze(-1).float()  # [batch_size, seq_len, 1]
            sum_encoded = torch.sum(encoded * mask_expanded, dim=1)  # [batch_size, d_model]
            sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)  # [batch_size, 1]
            pooled = sum_encoded / sum_mask  # [batch_size, d_model]
        else:
            pooled = encoded.mean(dim=1)

        pooled = self.dropout(pooled)
        logits = self.classifier(pooled)
        return logits


def get_model_summary(model: nn.Module) -> str:
    """Generate architecture summary and parameter counts."""
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    lines = [
        "=======================================================",
        "PhishSense Custom PyTorch Transformer Architecture",
        "=======================================================",
        str(model),
        "-------------------------------------------------------",
        f"Total Parameters:     {total_params:,}",
        f"Trainable Parameters: {trainable_params:,}",
        f"Embedding Dimension:  {model.d_model}",
        f"Classes:              {model.num_classes}",
        "=======================================================",
    ]
    return "\n".join(lines)
