"""Vocabulary builder, token indexer, and PyTorch Dataset for PhishSense."""
import json
import os
import re
from collections import Counter
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader

from .cleaner import unified_tokenize

SPECIAL_TOKENS = [
    "<pad>",
    "<unk>",
    "<url>",
    "<email>",
    "<phone>",
    "<routing>",
    "<date>",
    "<time>",
    "<year>",
    "<num>",
    "<footer_marker>",
]

LABEL2ID = {"safe": 0, "phishing": 1}
ID2LABEL = {0: "safe", 1: "phishing"}


class EmailVocabulary:
    def __init__(self, min_freq: int = 2, max_vocab: int = 30000):
        self.min_freq = min_freq
        self.max_vocab = max_vocab
        self.token2id = {}
        self.id2token = {}
        self.pad_token = "<pad>"
        self.unk_token = "<unk>"
        self.pad_id = 0
        self.unk_id = 1

    def fit(self, texts: list[str]) -> "EmailVocabulary":
        """Build vocabulary strictly from training texts."""
        counter = Counter()
        for text in texts:
            tokens = unified_tokenize(text)
            counter.update(tokens)

        # Initialize with special tokens
        self.token2id = {}
        self.id2token = {}
        for idx, token in enumerate(SPECIAL_TOKENS):
            self.token2id[token] = idx
            self.id2token[idx] = token

        curr_id = len(SPECIAL_TOKENS)

        # Sort remaining tokens by frequency
        for token, count in counter.most_common():
            if curr_id >= self.max_vocab:
                break
            if token in self.token2id:
                continue
            if count >= self.min_freq:
                self.token2id[token] = curr_id
                self.id2token[curr_id] = token
                curr_id += 1

        return self

    def encode(self, text: str, max_len: int = 256) -> tuple[list[int], list[int]]:
        """Encode text to token ids and attention mask with truncation and padding."""
        tokens = unified_tokenize(text)
        token_ids = [self.token2id.get(t, self.unk_id) for t in tokens[:max_len]]
        attention_mask = [1] * len(token_ids)

        # Pad to max_len
        pad_len = max_len - len(token_ids)
        if pad_len > 0:
            token_ids.extend([self.pad_id] * pad_len)
            attention_mask.extend([0] * pad_len)

        return token_ids, attention_mask

    def decode(self, token_ids: list[int]) -> list[str]:
        """Decode token ids to list of tokens."""
        return [self.id2token.get(idx, self.unk_token) for idx in token_ids if idx != self.pad_id]

    def save(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"token2id": self.token2id, "min_freq": self.min_freq, "max_vocab": self.max_vocab}, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "EmailVocabulary":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        vocab = cls(min_freq=data.get("min_freq", 2), max_vocab=data.get("max_vocab", 30000))
        vocab.token2id = data["token2id"]
        vocab.id2token = {int(v): k for k, v in vocab.token2id.items()}
        return vocab

    def __len__(self):
        return len(self.token2id)


class EmailDataset(Dataset):
    def __init__(self, texts: list[str], labels: list[str], vocab: EmailVocabulary, max_len: int = 256):
        self.texts = texts
        self.labels = [LABEL2ID[lbl.strip().lower()] for lbl in labels]
        self.vocab = vocab
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        token_ids, attention_mask = self.vocab.encode(text, max_len=self.max_len)
        return {
            "input_ids": torch.tensor(token_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "label": torch.tensor(label, dtype=torch.long),
        }


def compute_sequence_statistics(texts: list[str]) -> dict:
    """Compute token count percentiles strictly on training data."""
    lengths = [len(unified_tokenize(t)) for t in texts]
    return {
        "mean_len": float(np.mean(lengths)),
        "median_len": float(np.median(lengths)),
        "p90": float(np.percentile(lengths, 90)),
        "p95": float(np.percentile(lengths, 95)),
        "p99": float(np.percentile(lengths, 99)),
        "max_len": int(np.max(lengths)),
        "min_len": int(np.min(lengths)),
    }
