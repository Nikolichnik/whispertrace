"""
Training service for WhisperTrace.
"""

from logging import getLogger

from torch import Tensor, save
from torch.cuda import is_available as is_cuda_available
from torch.optim import Adam
from torch.nn import CrossEntropyLoss
from torch.utils.data import DataLoader

from common.constants import (
    DEVICE_CUDA,
    DEVICE_CPU,
    KEY_MODEL,
    KEY_VOCAB,
    DIR_CORPORA,
    DIR_CHECKPOINTS,
    EXTENSION_TXT,
    EXTENSION_PT,
    SPACER_DEFAULT,
    CHECKPOINT_NAME_DEFAULT,
    FORMAT_CHECKPOINT_NAME,
)

from domain.checkpoint import Checkpoint

from util.path import get_resource_path
from util.io import read_resource_file, get_resource_children

from dataset.lm_dataset import LMDataset, collate_batch

from lm.word_lstm import WordLSTM


logger = getLogger(__file__)

DEVICE = DEVICE_CUDA if is_cuda_available() else DEVICE_CPU


class CheckpointService:
    """
    Service for training models - working with checkpoints.
    """

    def create(
        self,
        checkpoint: Checkpoint,
    ) -> Checkpoint:
        """
        Train a language model on a specified corpus.

        Args:
            checkpoint (Checkpoint): The checkpoint configuration.

        Returns:
            Checkpoint: The created checkpoint object.
        """
        logger.debug(
            "Training LM checkpoint on %s for %d epochs using %s.",
            checkpoint.corpus, checkpoint.epochs, DEVICE,
        )

        text = read_resource_file(DIR_CORPORA, f"{checkpoint.corpus}{EXTENSION_TXT}").splitlines()
        n = len(text)
        n_train = int(0.7 * n)
        train_lines = text[:n_train]

        train_ds = LMDataset(train_lines)

        vocab = train_ds.vocab
        model = WordLSTM(vocab_size=len(vocab.itos)).to(DEVICE)

        opt = Adam(model.parameters(), lr=checkpoint.learning_rate)

        train_loader = DataLoader(
            dataset=train_ds,
            batch_size=checkpoint.batch_size,
            shuffle=True,
            collate_fn=collate_batch,
        )

        for epoch in range(1, checkpoint.epochs + 1):
            model.train()
            total = 0
            steps = 0

            for xs, ys, mask in train_loader:
                xs, ys, mask = xs.to(DEVICE), ys.to(DEVICE), mask.to(DEVICE)
                logits, _ = model(xs)
                loss = self._loss_for_batch(logits, ys, mask)
                opt.zero_grad()
                loss.backward()
                opt.step()
                total += loss.item()
                steps += 1

            logger.debug("Epoch %d completed. Average train loss: %.4f", epoch, total/max(1, steps))

        checkpoint.name = checkpoint.name or CHECKPOINT_NAME_DEFAULT

        checkpoint_name = FORMAT_CHECKPOINT_NAME.format(
            name_prefix=f"{checkpoint.name}{SPACER_DEFAULT}" if checkpoint.name else "",
            corpus=checkpoint.corpus,
            epochs=checkpoint.epochs,
            batch_size=checkpoint.batch_size,
            learning_rate=checkpoint.learning_rate,
        )
        output_path = f"{get_resource_path(DIR_CHECKPOINTS)}/{checkpoint_name}{EXTENSION_PT}"

        save(
            obj={
                KEY_MODEL: model.state_dict(),
                KEY_VOCAB: vocab.itos,
            },
            f=output_path,
        )

        logger.debug("Model trained and saved to %s", output_path)

        return Checkpoint(
            name=checkpoint_name,
            corpus=checkpoint.corpus,
            epochs=checkpoint.epochs,
            batch_size=checkpoint.batch_size,
            learning_rate=checkpoint.learning_rate,
        )

    def get_all(self) -> list[Checkpoint]:
        """
        Get a list of available model checkpoints.

        Returns:
            list[Checkpoint]: List of checkpoints.
        """
        logger.debug("Retrieving list of available checkpoints...")

        checkpoint_file_names: list[str] = get_resource_children(DIR_CHECKPOINTS)
        checkpoints = []

        for checkpoint_file_name in checkpoint_file_names:
            name = checkpoint_file_name.split(EXTENSION_PT)[0]
            name_parts = name.split(SPACER_DEFAULT)

            checkpoints.append(
                Checkpoint(
                    name=name,
                    corpus=name_parts[-4],
                    epochs=int(name_parts[-3]),
                    batch_size=int(name_parts[-2]),
                    learning_rate=float(name_parts[-1]),
                )
            )

        logger.debug("Retrieved %d checkpoints.", len(checkpoints))

        return checkpoints

    # pylint: disable=invalid-name
    def _loss_for_batch(
        self,
        logits: Tensor,
        y: Tensor,
        mask: Tensor,
    ) -> Tensor:
        """
        Compute the loss for a batch of sequences.

        Args:
            logits (Tensor): The model's output logits of shape (B, T, V).
            y (Tensor): The target token indices of shape (B, T).
            mask (Tensor): The mask indicating valid tokens of shape (B, T).

        Returns:
            Tensor: The average loss over the batch.
        """
        B,T,V = logits.shape
        criterion = CrossEntropyLoss(ignore_index=0, reduction="none")
        loss = criterion(logits.reshape(B*T, V), y.reshape(B*T))
        loss = loss.view(B,T)
        seq_loss = (loss*mask).sum(dim=1)/(mask.sum(dim=1)+1e-8)

        return seq_loss.mean()
