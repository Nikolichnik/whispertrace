"""
Vocabulary class for token to index mapping and vice versa.
"""

from collections import Counter


class Vocab:
    """
    Vocabulary class for token to index mapping and vice versa.
    """
    def __init__(self, tokens, min_freq=1):
        cnt = Counter(tokens)
        self.itos = ["<pad>","<bos>","<eos>","<unk>"]

        for t,f in cnt.items():
            if f >= min_freq and t not in self.itos:
                self.itos.append(t)

        self.stoi = {t:i for i,t in enumerate(self.itos)}

    def encode(self, tokens: list[str]) -> list[int]:
        """
        Encode a list of tokens to their corresponding indices.

        Args:
            tokens (list[str]): List of tokens to encode.

        Returns:
            list[int]: List of token indices.
        """
        return [self.stoi.get(t, self.stoi["<unk>"]) for t in tokens]

    def decode(self, ids: list[int]) -> list[str]:
        """
        Decode a list of token indices to their corresponding tokens.

        Args:
            ids (list[int]): List of token indices to decode.

        Returns:
            list[str]: List of decoded tokens.
        """
        return [self.itos[i] for i in ids]


class RestoredVocab:
    """
    Rebuild a minimal Vocab from a saved itos list (indices-to-string).
    Provides stoi, encode, decode so LMDataset can use it.
    """
    def __init__(self, itos):
        self.itos = list(itos)
        self.stoi = {t: i for i, t in enumerate(self.itos)}

        # ensure special tokens exist
        for tok in ["<pad>", "<bos>", "<eos>", "<unk>"]:
            if tok not in self.stoi:
                self.stoi[tok] = len(self.itos)
                self.itos.append(tok)

        # pad index is assumed 0 in collate_batch; keep it that way if possible
        if self.itos[0] != "<pad>":
            # swap to make "<pad>" at index 0
            pad_idx = self.stoi["<pad>"]
            self.itos[0], self.itos[pad_idx] = self.itos[pad_idx], self.itos[0]
            # rebuild stoi
            self.stoi = {t: i for i, t in enumerate(self.itos)}

    def encode(self, tokens: list[str]) -> list[int]:
        """
        Encode a list of tokens to their corresponding indices.

        Args:
            tokens (list[str]): List of tokens to encode.

        Returns:
            list[int]: List of token indices.
        """
        unk = self.stoi.get("<unk>", 0)
        return [self.stoi.get(t, unk) for t in tokens]

    def decode(self, ids: list[int]) -> list[str]:
        """
        Decode a list of token indices to their corresponding tokens.

        Args:
            ids (list[int]): List of token indices to decode.

        Returns:
            list[str]: List of decoded tokens.
        """
        return [self.itos[i] if 0 <= i < len(self.itos) else "<unk>" for i in ids]
