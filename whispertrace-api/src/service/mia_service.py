"""
This module contains the Membership Inference Attack (MIA) service.
"""

from logging import getLogger

from datetime import datetime

from torch import Tensor, device, no_grad, load
from torch.nn import CrossEntropyLoss
from torch.cuda import is_available as is_cuda_available
from torch.utils.data import DataLoader

from sklearn.metrics import roc_auc_score

import numpy as np

import pandas as pd

from common.constants import (
    DEVICE_CUDA,
    DEVICE_CPU,
    DIR_CORPORA,
    DIR_CHECKPOINTS,
    DIR_MIAS,
    EXTENSION_TXT,
    EXTENSION_PT,
    EXTENSION_CSV,
    FORMAT_DATETIME,
    FORMAT_MIA_DIR_NAME,
    MIA_THRESHOLD,
    SPACER_DEFAULT,
)

from domain.mia import Mia, Sentence

from dataset.lm_dataset import LMDataset, collate_batch

from vocab.vocab import RestoredVocab

from lm.word_lstm import WordLSTM

from util.path import get_resource_path, ensure_dir
from util.io import get_resource_children, read_resource_file, save_csv_table, save_plots


logger = getLogger(__file__)

DEVICE = DEVICE_CUDA if is_cuda_available() else DEVICE_CPU


class MiaService:
    """
    Service for performing Membership Inference Attacks (MIA) on language models.
    """

    def perform(
        self,
        mia: Mia,
    ) -> Mia:
        """
        Perform a membership inference attack on the specified
        checkpoint using the provided test data.

        Args:
            mia (Mia): The MIA configuration.

        Returns:
            Mia: The information about the newly performed MIA.
        """
        logger.debug(
            "Performing MIA on checkpoint %s using corpus %s with batch size %d.",
            mia.checkpoint, mia.corpus, mia.batch_size,
        )

        # Load corpus and split (train = members, held-out = non-members)
        lines = [
            line
            for line in read_resource_file(DIR_CORPORA, f"{mia.corpus}{EXTENSION_TXT}").splitlines() if line.strip()
        ]
        n = len(lines)
        n_train = int(0.7 * n)
        train_lines = lines[:n_train]
        held_lines  = lines[n_train:]

        # Restore model + vocab
        checkpoint_path = f"{get_resource_path(DIR_CHECKPOINTS)}/{mia.checkpoint}{EXTENSION_PT}"
        checkpoint = load(checkpoint_path, map_location="cpu")
        vocab = RestoredVocab(checkpoint["vocab"])

        # Build datasets that use the restored vocab
        train_ds = LMDataset(train_lines, vocab=vocab)
        held_ds  = LMDataset(held_lines,  vocab=vocab)

        model = WordLSTM(vocab_size=len(vocab.itos)).to(DEVICE)
        model.load_state_dict(checkpoint["model"])
        model.eval()

        # Compute per-sequence losses
        train_losses = self._losses_for_dataset(model, train_ds, mia.batch_size, DEVICE)
        held_losses  = self._losses_for_dataset(model, held_ds,  mia.batch_size, DEVICE)

        # Membership scores: lower loss ⇒ higher membership likelihood
        y_true = np.array([1]*len(train_losses) + [0] * len(held_losses))  # 1=member
        scores = -np.concatenate([train_losses, held_losses])
        mia.auc = roc_auc_score(y_true, scores)

        # Sentences to score
        if mia.input:
            sentences = mia.input.strip().split("|")
        else:
            # If no input provided, use some training and held-out examples + some random sentences.
            sentences = [
                train_lines[0] if train_lines else "Alice paints portraits in watercolor at dawn.",
                "Are you suggesting coconuts migrate?",
                held_lines[0]  if held_lines  else "Mallory composes melodies with strings on weekends.",
                "Just a flesh wound.",
                "Alice writes essays in watercolor at dawn.",
                "Nikola builds AI pipelines on GCP with privacy-first design.",
                "Carol designs landscapes in charcoal on weekends.",
                "Well, she turned me into a newt!",
                "Ni!",
            ]

        # Score sentences
        mia.sentences = []
        results = []

        for sentence in sentences:
            score = self._score_sentence(
                model=model,
                vocab=vocab,
                sentence=sentence,
            )
            rounded_score = round(score, 3)
            normalized_score = max(0, min(1, (score + 17) / 17))
            is_member = normalized_score > MIA_THRESHOLD

            sentence = Sentence(
                content=sentence,
                is_member=is_member,
                score=rounded_score,
                normalized_score=round(normalized_score, 3),
            )

            mia.sentences.append(sentence)
            results.append(sentence.dict())

        # Log and save output
        timestamp = datetime.now().strftime(FORMAT_DATETIME)
        mia.timestamp = timestamp

        output_dir_name = FORMAT_MIA_DIR_NAME.format(
            datetime=timestamp,
            checkpoint=mia.checkpoint,
            corpus=mia.corpus,
            batch_size=mia.batch_size,
            auc=f"{mia.auc:.3f}",
        )
        output_dir = f"{get_resource_path(DIR_MIAS)}/{output_dir_name}"
        ensure_dir(output_dir)
        output_path = f"{output_dir}/output"
        csv_path = f"{output_path}{EXTENSION_CSV}"

        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False)

        save_csv_table(
            csv_path=csv_path,
            output_path=f"{output_path}{EXTENSION_TXT}",
            percentage_columns=["normalized_score"],
            highlight_threshold=MIA_THRESHOLD,
        )

        save_plots(
            train_losses=train_losses,
            held_losses=held_losses,
            y_true=y_true,
            scores=scores,
            output_dir=output_dir,
        )

        return mia

    def get_all(self) -> list[Mia]:
        """
        Get a list of all performed MIAs.

        Returns:
            list[Mia]: List of performed MIAs.
        """
        logger.debug("Retrieving list of performed MIAs...")

        mia_dir_names = get_resource_children(DIR_MIAS)
        mias = []

        for mia_dir_name in mia_dir_names:
            try:
                parts = mia_dir_name.split(SPACER_DEFAULT)

                mias.append(
                    Mia(
                        checkpoint=SPACER_DEFAULT.join(parts[1:-3]),
                        corpus=parts[-3],
                        batch_size=int(parts[-2]),
                        auc=float(parts[-1]),
                        timestamp=parts[0],
                    )
                )
            except (IndexError, ValueError) as e:
                logger.warning("Skipping invalid MIA directory name '%s': %s", mia_dir_name, e)

        logger.debug("Retrieved %d MIAs.", len(mias))

        return sorted(mias, key=lambda x: x.checkpoint)

    # pylint: disable=redefined-outer-name, invalid-name
    def _per_sequence_loss(
        self,
        model: WordLSTM,
        batch: tuple[Tensor, Tensor, Tensor],
        device: device,
    ) -> np.ndarray:
        """
        Compute the per-sequence loss for a batch.

        Args:
            model (WordLSTM): The language model.
            batch (tuple[Tensor, Tensor, Tensor]): A batch of (inputs, targets, mask).
            device (device): The device to run the computation on.

        Returns:
            np.ndarray: The per-sequence losses as a numpy array.
        """
        xs, ys, mask = batch
        xs, ys, mask = xs.to(device), ys.to(device), mask.to(device)
        criterion = CrossEntropyLoss(ignore_index=0, reduction="none")

        with no_grad():
            logits, _ = model(xs)
            B, T, V = logits.shape
            loss = criterion(logits.reshape(B*T, V), ys.reshape(B*T)).view(B, T)
            seq_loss = (loss * mask).sum(dim=1) / (mask.sum(dim=1) + 1e-8)

            return seq_loss.cpu().numpy()

    def _losses_for_dataset(
        self,
        model: WordLSTM,
        dataset: LMDataset,
        batch_size: int,
        device: device,
    ) -> np.ndarray:
        """
        Compute the losses for a dataset by batching.

        Args:
            model (WordLSTM): The language model.
            dataset (LMDataset): The dataset to compute losses for.
            batch_size (int): The batch size for DataLoader.
            device (device): The device to run the computation on.

        Returns:
            np.ndarray: The per-sequence losses for the entire dataset.
        """
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_batch)
        all_losses = []

        for batch in loader:
            all_losses.append(self._per_sequence_loss(model, batch, device))

        return np.concatenate(all_losses, axis=0)

    def _score_sentence(
        self,
        model: WordLSTM,
        vocab: RestoredVocab,
        sentence: str,
    ) -> float:
        """
        Compute the membership score for a single sentence.

        Args:
            model (WordLSTM): The language model.
            vocab (RestoredVocab): The vocabulary for tokenization.
            sentence (str): The input sentence.

        Returns:
            float: The membership score (negative loss).
        """
        dataset = LMDataset([sentence], vocab=vocab)
        xs, ys, mask = collate_batch([dataset[0]])

        return -self._per_sequence_loss(model, (xs, ys, mask), DEVICE)[0]
