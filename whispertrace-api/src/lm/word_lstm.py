"""
A simple word-level LSTM language model.
"""

from torch import Tensor, nn

class WordLSTM(nn.Module):
    """
    A simple word-level LSTM language model.
    """
    def __init__(self, vocab_size, emb=128, hidden=256):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb)
        self.lstm = nn.LSTM(emb, hidden, batch_first=True)
        self.head = nn.Linear(hidden, vocab_size)

    def forward(self, x: Tensor, h: Tensor = None):
        """
        Forward pass for the LSTM.

        Args:
            x (Tensor): Input tensor of shape (B, T) where B is batch size
                        and T is sequence length.
            h (Tensor, optional): Initial hidden state. Defaults to None.

        Returns:
            Tuple[Tensor, Tensor]: Output logits of shape (B, T, V) and
                                   final hidden state.
        """
        e = self.emb(x)
        y, h = self.lstm(e, h)
        logits = self.head(y)

        return logits, h
