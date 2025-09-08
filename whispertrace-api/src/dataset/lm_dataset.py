"""
LM dataset and utilities.
"""

import re

import torch
from torch import Tensor
from torch.utils.data import Dataset

from vocab.vocab import Vocab


def tokenize(s: str) -> list[str]:
    """
    Tokenizes input string into a list of tokens.

    Args:
        s (str): The input string.

    Returns:
        list[str]: List of tokens.
    """
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s\.]", "", s)
    s = s.replace(".", " .")
    tokens = s.split()

    return tokens


def collate_batch(batch: list[Tensor]) -> tuple[Tensor, Tensor, Tensor]:
    """
    Collates a batch of sequences into a padded tensor.

    Args:
        batch (list[Tensor]): List of 1D tensors (sequences of token indices
                              of varying lengths).

    Returns:
        tuple[Tensor, Tensor, Tensor]: Padded input tensor (xs), target tensor (ys),
                                       and mask tensor.
    """
    maxlen = max(len(x) for x in batch)
    pad = 0
    xs = torch.full((len(batch), maxlen), pad, dtype=torch.long)
    ys = torch.full((len(batch), maxlen), pad, dtype=torch.long)

    for i, seq in enumerate(batch):
        xs[i,:len(seq)-1] = seq[:-1]
        ys[i,:len(seq)-1] = seq[1:]

    mask = (xs != pad).float()

    return xs, ys, mask

class LMDataset(Dataset):
    """
    Language Model Dataset.
    """
    def __init__(self, lines, vocab=None):
        token = []

        for line in lines:
            line = line.strip()

            if not line:
                continue

            token.extend(tokenize(line))

        if vocab is None:
            vocab = Vocab(token)

        self.vocab = vocab
        self.samples = []

        for line in lines:
            line = line.strip()

            if not line:
                continue

            t = ["<bos>"] + tokenize(line) + ["<eos>"]
            ids = self.vocab.encode(t)

            self.samples.append(torch.tensor(ids, dtype=torch.long))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, i):
        return self.samples[i]
