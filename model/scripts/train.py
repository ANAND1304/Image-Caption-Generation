"""
Image Caption Generator - Training Pipeline
Architecture: ResNet50 (CNN) + Attention + LSTM
Dataset: Flickr8k / Flickr30k
Paper: "Show, Attend and Tell" (Xu et al., 2015)
"""

import os
import sys
import json
import pickle
import logging
import argparse
import time
from pathlib import Path
from collections import Counter

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pack_padded_sequence
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from nltk.translate.bleu_score import corpus_bleu

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------
class Vocabulary:
    """Word-to-index and index-to-word mappings."""

    PAD_TOKEN = "<pad>"  # 0
    START_TOKEN = "<start>"  # 1
    END_TOKEN = "<end>"  # 2
    UNK_TOKEN = "<unk>"  # 3

    def __init__(self, freq_threshold: int = 5):
        self.freq_threshold = freq_threshold
        self.word2idx = {}
        self.idx2word = {}
        self.word_freq = Counter()
        # Reserve special tokens
        for i, tok in enumerate([self.PAD_TOKEN, self.START_TOKEN,
                                  self.END_TOKEN, self.UNK_TOKEN]):
            self.word2idx[tok] = i
            self.idx2word[i] = tok

    def build(self, captions: list[str]) -> None:
        """Build vocab from list of caption strings."""
        for cap in captions:
            self.word_freq.update(cap.lower().split())
        idx = len(self.word2idx)
        for word, freq in self.word_freq.items():
            if freq >= self.freq_threshold and word not in self.word2idx:
                self.word2idx[word] = idx
                self.idx2word[idx] = word
                idx += 1
        logger.info(f"Vocabulary size: {len(self.word2idx)}")

    def encode(self, caption: str, max_len: int = 50) -> list[int]:
        """Encode caption string to list of token ids."""
        tokens = caption.lower().split()[:max_len - 2]
        ids = ([self.word2idx[self.START_TOKEN]]
               + [self.word2idx.get(w, self.word2idx[self.UNK_TOKEN])
                  for w in tokens]
               + [self.word2idx[self.END_TOKEN]])
        return ids

    def decode(self, ids: list[int]) -> str:
        """Decode token ids back to caption string."""
        words = []
        for i in ids:
            word = self.idx2word.get(i, self.UNK_TOKEN)
            if word == self.END_TOKEN:
                break
            if word not in (self.START_TOKEN, self.PAD_TOKEN):
                words.append(word)
        return " ".join(words)

    def __len__(self):
        return len(self.word2idx)

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path: str) -> "Vocabulary":
        with open(path, "rb") as f:
            return pickle.load(f)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
class Flickr8kDataset(Dataset):
    """
    Flickr8k Dataset loader.
    Expected captions file format (one per line):
        image_name.jpg,caption text here
    """

    def __init__(self, images_dir: str, captions_file: str,
                 vocab: Vocabulary, max_len: int = 50,
                 split: str = "train", transform=None):
        self.images_dir = Path(images_dir)
        self.vocab = vocab
        self.max_len = max_len
        self.transform = transform or self._default_transform(split)

        # Parse captions
        self.data = []
        with open(captions_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("image"):
                    continue
                parts = line.split(",", 1)
                if len(parts) != 2:
                    continue
                img_name, caption = parts
                img_path = self.images_dir / img_name.strip()
                if img_path.exists():
                    self.data.append((str(img_path), caption.strip()))

        logger.info(f"Loaded {len(self.data)} samples for split={split}")

    @staticmethod
    def _default_transform(split: str):
        if split == "train":
            return transforms.Compose([
                transforms.Resize((256, 256)),
                transforms.RandomCrop(224),
                transforms.RandomHorizontalFlip(),
                transforms.ColorJitter(brightness=0.3, contrast=0.3),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
            ])
        else:
            return transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
            ])

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        img_path, caption = self.data[idx]
        image = Image.open(img_path).convert("RGB")
        image = self.transform(image)

        # Encode caption
        ids = self.vocab.encode(caption, self.max_len)
        # Pad to max_len
        ids = ids + [self.vocab.word2idx[Vocabulary.PAD_TOKEN]] * (self.max_len - len(ids))
        ids = ids[:self.max_len]

        return image, torch.tensor(ids, dtype=torch.long), len(ids)


def collate_fn(batch):
    """Sort batch by caption length descending (for pack_padded_sequence)."""
    images, captions, lengths = zip(*batch)
    images = torch.stack(images, 0)
    captions = torch.stack(captions, 0)
    lengths = torch.tensor(lengths)
    # Sort
    lengths, sort_idx = lengths.sort(descending=True)
    images = images[sort_idx]
    captions = captions[sort_idx]
    return images, captions, lengths


# ---------------------------------------------------------------------------
# Model Components
# ---------------------------------------------------------------------------
class EncoderCNN(nn.Module):
    """
    ResNet50 feature extractor.
    Outputs spatial feature maps: (batch, 14*14, 2048)
    """

    def __init__(self, encoded_image_size: int = 14):
        super().__init__()
        resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
        # Remove avgpool and fc layers — keep spatial features
        modules = list(resnet.children())[:-2]
        self.resnet = nn.Sequential(*modules)
        self.adaptive_pool = nn.AdaptiveAvgPool2d((encoded_image_size,
                                                   encoded_image_size))
        self.fine_tune(fine_tune=True)

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        """
        Args:
            images: (batch, 3, 224, 224)
        Returns:
            features: (batch, encoded_size*encoded_size, 2048)
        """
        features = self.resnet(images)         # (B, 2048, 7, 7)
        features = self.adaptive_pool(features) # (B, 2048, 14, 14)
        features = features.permute(0, 2, 3, 1) # (B, 14, 14, 2048)
        batch_size, h, w, ch = features.size()
        features = features.view(batch_size, -1, ch)  # (B, 196, 2048)
        return features

    def fine_tune(self, fine_tune: bool = True) -> None:
        """Freeze/unfreeze ResNet layers."""
        for p in self.resnet.parameters():
            p.requires_grad = False
        # Unfreeze layer3 and layer4
        if fine_tune:
            for c in list(self.resnet.children())[5:]:
                for p in c.parameters():
                    p.requires_grad = True


class BahdanauAttention(nn.Module):
    """
    Bahdanau (additive) Attention Mechanism.
    Computes a context vector as a weighted sum of encoder features.
    """

    def __init__(self, encoder_dim: int, decoder_dim: int, attention_dim: int):
        super().__init__()
        self.encoder_att = nn.Linear(encoder_dim, attention_dim)
        self.decoder_att = nn.Linear(decoder_dim, attention_dim)
        self.full_att = nn.Linear(attention_dim, 1)
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)

    def forward(self, encoder_out: torch.Tensor,
                decoder_hidden: torch.Tensor):
        """
        Args:
            encoder_out: (batch, num_pixels, encoder_dim)
            decoder_hidden: (batch, decoder_dim)
        Returns:
            context: (batch, encoder_dim)
            alpha: (batch, num_pixels)  — attention weights
        """
        att1 = self.encoder_att(encoder_out)             # (B, P, att_dim)
        att2 = self.decoder_att(decoder_hidden).unsqueeze(1)  # (B, 1, att_dim)
        att = self.full_att(self.relu(att1 + att2)).squeeze(2)  # (B, P)
        alpha = self.softmax(att)                        # (B, P)
        context = (encoder_out * alpha.unsqueeze(2)).sum(1)  # (B, encoder_dim)
        return context, alpha


class DecoderWithAttention(nn.Module):
    """
    LSTM Decoder with Bahdanau Attention.
    At each step, attends over encoder features to produce next word.
    """

    def __init__(self, attention_dim: int, embed_dim: int,
                 decoder_dim: int, vocab_size: int,
                 encoder_dim: int = 2048, dropout: float = 0.5):
        super().__init__()
        self.encoder_dim = encoder_dim
        self.attention_dim = attention_dim
        self.embed_dim = embed_dim
        self.decoder_dim = decoder_dim
        self.vocab_size = vocab_size

        self.attention = BahdanauAttention(encoder_dim, decoder_dim,
                                           attention_dim)
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.dropout = nn.Dropout(p=dropout)
        self.lstm_cell = nn.LSTMCell(embed_dim + encoder_dim, decoder_dim)

        # Initialize LSTM state from mean encoder output
        self.init_h = nn.Linear(encoder_dim, decoder_dim)
        self.init_c = nn.Linear(encoder_dim, decoder_dim)

        # Gating scalar — scales context vector
        self.f_beta = nn.Linear(decoder_dim, encoder_dim)
        self.sigmoid = nn.Sigmoid()

        # Output projection
        self.fc = nn.Linear(decoder_dim, vocab_size)
        self._init_weights()

    def _init_weights(self) -> None:
        self.embedding.weight.data.uniform_(-0.1, 0.1)
        self.fc.bias.data.fill_(0)
        self.fc.weight.data.uniform_(-0.1, 0.1)

    def init_hidden_state(self, encoder_out: torch.Tensor):
        """Initialize LSTM h & c from mean-pooled encoder features."""
        mean_enc = encoder_out.mean(dim=1)  # (B, encoder_dim)
        h = self.init_h(mean_enc)           # (B, decoder_dim)
        c = self.init_c(mean_enc)           # (B, decoder_dim)
        return h, c

    def forward(self, encoder_out: torch.Tensor,
                captions: torch.Tensor, lengths: torch.Tensor):
        """
        Teacher-forcing forward pass.
        Args:
            encoder_out: (B, num_pixels, encoder_dim)
            captions: (B, max_len) — padded token ids
            lengths: (B,) — actual lengths
        Returns:
            predictions: (sum_lengths, vocab_size)
            alphas: (B, max_len-1, num_pixels)
        """
        batch_size = encoder_out.size(0)
        num_pixels = encoder_out.size(1)

        embeddings = self.dropout(self.embedding(captions))  # (B, max_len, E)
        h, c = self.init_hidden_state(encoder_out)

        # We decode up to max(lengths)-1 steps (exclude <end> from input)
        decode_lengths = (lengths - 1).tolist()
        max_t = max(decode_lengths)

        predictions = torch.zeros(batch_size, max_t, self.vocab_size,
                                  device=encoder_out.device)
        alphas = torch.zeros(batch_size, max_t, num_pixels,
                             device=encoder_out.device)

        for t in range(max_t):
            # Only process samples whose true length > t
            batch_t = sum([l > t for l in decode_lengths])
            context, alpha = self.attention(encoder_out[:batch_t],
                                            h[:batch_t])
            gate = self.sigmoid(self.f_beta(h[:batch_t]))  # gating
            context = gate * context
            lstm_input = torch.cat([embeddings[:batch_t, t, :], context],
                                   dim=1)
            h, c = self.lstm_cell(lstm_input,
                                  (h[:batch_t], c[:batch_t]))
            preds = self.fc(self.dropout(h))  # (batch_t, vocab_size)
            predictions[:batch_t, t, :] = preds
            alphas[:batch_t, t, :] = alpha

        return predictions, alphas, decode_lengths


# ---------------------------------------------------------------------------
# Beam Search Inference
# ---------------------------------------------------------------------------
class CaptionGenerator:
    """Inference wrapper with Beam Search decoding."""

    def __init__(self, encoder: EncoderCNN, decoder: DecoderWithAttention,
                 vocab: Vocabulary, device: torch.device,
                 max_len: int = 50, beam_size: int = 3):
        self.encoder = encoder.to(device).eval()
        self.decoder = decoder.to(device).eval()
        self.vocab = vocab
        self.device = device
        self.max_len = max_len
        self.beam_size = beam_size
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

    @torch.no_grad()
    def generate(self, image: Image.Image,
                 beam_size: int = None) -> tuple[str, float]:
        """
        Generate caption for a PIL Image using Beam Search.
        Returns: (caption_string, confidence_score)
        """
        beam_size = beam_size or self.beam_size
        img_tensor = self.transform(image).unsqueeze(0).to(self.device)

        # Encode
        enc_out = self.encoder(img_tensor)  # (1, 196, 2048)
        enc_dim = enc_out.size(-1)
        num_pixels = enc_out.size(1)

        # Expand for beam search
        enc_out = enc_out.expand(beam_size, num_pixels, enc_dim)

        # Initialize beams: (score, sequence, h, c)
        start_id = self.vocab.word2idx[Vocabulary.START_TOKEN]
        end_id = self.vocab.word2idx[Vocabulary.END_TOKEN]

        h, c = self.decoder.init_hidden_state(enc_out)  # (B, dec_dim)
        k_prev_words = torch.tensor([[start_id]] * beam_size,
                                    device=self.device)  # (B, 1)

        seqs = k_prev_words  # (B, 1)
        top_k_scores = torch.zeros(beam_size, 1, device=self.device)

        complete_seqs = []
        complete_seqs_scores = []

        for step in range(self.max_len):
            embeddings = self.decoder.embedding(
                k_prev_words.squeeze(1))          # (B, E)
            context, _ = self.decoder.attention(enc_out, h)
            gate = self.decoder.sigmoid(self.decoder.f_beta(h))
            context = gate * context
            h, c = self.decoder.lstm_cell(
                torch.cat([embeddings, context], dim=1), (h, c))
            scores = self.decoder.fc(h)          # (B, vocab)
            scores = torch.log_softmax(scores, dim=1)
            scores = top_k_scores.expand_as(scores) + scores

            if step == 0:
                top_k_scores, top_k_words = scores[0].topk(beam_size)
            else:
                top_k_scores, top_k_words = scores.view(-1).topk(beam_size)

            prev_word_inds = top_k_words // len(self.vocab)
            next_word_inds = top_k_words % len(self.vocab)

            seqs = torch.cat([seqs[prev_word_inds], next_word_inds.unsqueeze(1)],
                             dim=1)
            h = h[prev_word_inds]
            c = c[prev_word_inds]
            enc_out = enc_out[prev_word_inds]

            # Find complete sequences
            incomplete = []
            for i, word in enumerate(next_word_inds.tolist()):
                if word == end_id:
                    complete_seqs.append(seqs[i].tolist())
                    complete_seqs_scores.append(top_k_scores[i].item())
                else:
                    incomplete.append(i)

            if not incomplete:
                break

            # Keep only incomplete beams
            seqs = seqs[incomplete]
            h = h[incomplete]
            c = c[incomplete]
            enc_out = enc_out[incomplete]
            top_k_scores = top_k_scores[incomplete].unsqueeze(1)
            k_prev_words = next_word_inds[incomplete].unsqueeze(1)
            beam_size = len(incomplete)

            if beam_size == 0:
                break

        if not complete_seqs:
            complete_seqs = [seqs[0].tolist()]
            complete_seqs_scores = [top_k_scores[0].item()]

        best_idx = complete_seqs_scores.index(max(complete_seqs_scores))
        best_seq = complete_seqs[best_idx]
        caption = self.vocab.decode(best_seq)

        # Normalize score to [0,1] confidence
        norm_score = min(1.0, max(0.0,
                         (complete_seqs_scores[best_idx] / -self.max_len + 1)))
        return caption, float(norm_score)


# ---------------------------------------------------------------------------
# Training Loop
# ---------------------------------------------------------------------------
class Trainer:
    def __init__(self, args):
        self.args = args
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")

    def run(self):
        args = self.args
        # Build vocabulary
        vocab = self._build_vocab()

        # Datasets
        train_dataset = Flickr8kDataset(
            args.images_dir, args.captions_file, vocab,
            max_len=args.max_len, split="train")
        val_dataset = Flickr8kDataset(
            args.images_dir, args.val_captions_file or args.captions_file,
            vocab, max_len=args.max_len, split="val")

        train_loader = DataLoader(train_dataset, batch_size=args.batch_size,
                                  shuffle=True, collate_fn=collate_fn,
                                  num_workers=4, pin_memory=True)
        val_loader = DataLoader(val_dataset, batch_size=args.batch_size,
                                shuffle=False, collate_fn=collate_fn,
                                num_workers=4, pin_memory=True)

        # Models
        encoder = EncoderCNN().to(self.device)
        decoder = DecoderWithAttention(
            attention_dim=args.attention_dim,
            embed_dim=args.embed_dim,
            decoder_dim=args.decoder_dim,
            vocab_size=len(vocab),
            dropout=args.dropout
        ).to(self.device)

        # Optimizers (separate LR for encoder fine-tuning)
        decoder_optimizer = optim.Adam(
            decoder.parameters(), lr=args.decoder_lr)
        encoder_optimizer = optim.Adam(
            filter(lambda p: p.requires_grad, encoder.parameters()),
            lr=args.encoder_lr) if args.fine_tune_encoder else None

        criterion = nn.CrossEntropyLoss(
            ignore_index=vocab.word2idx[Vocabulary.PAD_TOKEN])

        best_bleu4 = 0.0
        Path(args.save_dir).mkdir(parents=True, exist_ok=True)

        for epoch in range(1, args.epochs + 1):
            train_loss = self._train_epoch(
                encoder, decoder, train_loader,
                decoder_optimizer, encoder_optimizer, criterion, epoch)
            bleu4 = self._validate(encoder, decoder, val_loader, vocab)
            logger.info(
                f"Epoch {epoch}/{args.epochs} | "
                f"Train Loss: {train_loss:.4f} | BLEU-4: {bleu4:.4f}")

            if bleu4 > best_bleu4:
                best_bleu4 = bleu4
                self._save(encoder, decoder, vocab, args.save_dir, epoch, bleu4)

        logger.info(f"Training complete. Best BLEU-4: {best_bleu4:.4f}")

    def _train_epoch(self, encoder, decoder, loader,
                     dec_opt, enc_opt, criterion, epoch):
        encoder.train()
        decoder.train()
        total_loss = 0

        for i, (imgs, caps, lengths) in enumerate(loader):
            imgs = imgs.to(self.device)
            caps = caps.to(self.device)
            lengths = lengths.to(self.device)

            enc_out = encoder(imgs)
            preds, alphas, decode_lengths = decoder(enc_out, caps, lengths)

            # Pack predictions and targets
            targets = caps[:, 1:]  # shift right — remove <start>
            preds_packed = pack_padded_sequence(
                preds, decode_lengths, batch_first=True).data
            targets_packed = pack_padded_sequence(
                targets, decode_lengths, batch_first=True).data

            loss = criterion(preds_packed, targets_packed)

            # Doubly stochastic attention regularization
            alpha_reg = ((1. - alphas.sum(dim=1)) ** 2).mean()
            loss += 1.0 * alpha_reg

            dec_opt.zero_grad()
            if enc_opt:
                enc_opt.zero_grad()
            loss.backward()

            # Gradient clipping
            nn.utils.clip_grad_norm_(decoder.parameters(), 5.0)
            if enc_opt:
                nn.utils.clip_grad_norm_(encoder.parameters(), 5.0)

            dec_opt.step()
            if enc_opt:
                enc_opt.step()

            total_loss += loss.item()
            if i % 100 == 0:
                logger.info(f"  Step {i}/{len(loader)} | Loss: {loss.item():.4f}")

        return total_loss / len(loader)

    @torch.no_grad()
    def _validate(self, encoder, decoder, loader, vocab):
        """Compute BLEU-4 on validation set."""
        encoder.eval()
        decoder.eval()
        gen = CaptionGenerator(encoder, decoder, vocab,
                               self.device, beam_size=3)
        references = []
        hypotheses = []

        for imgs, caps, lengths in loader:
            imgs_pil = [transforms.ToPILImage()(img) for img in imgs]
            for pil_img, cap, length in zip(imgs_pil, caps, lengths):
                cap_str = vocab.decode(cap[:length].tolist())
                references.append([cap_str.split()])
                hyp, _ = gen.generate(pil_img)
                hypotheses.append(hyp.split())
            if len(hypotheses) >= 500:  # quick eval
                break

        bleu4 = corpus_bleu(references, hypotheses)
        return bleu4

    def _build_vocab(self):
        args = self.args
        vocab_path = Path(args.save_dir) / "vocab.pkl"
        if vocab_path.exists():
            logger.info("Loading existing vocabulary...")
            return Vocabulary.load(str(vocab_path))

        captions = []
        with open(args.captions_file) as f:
            for line in f:
                parts = line.strip().split(",", 1)
                if len(parts) == 2:
                    captions.append(parts[1].strip())

        vocab = Vocabulary(freq_threshold=args.freq_threshold)
        vocab.build(captions)
        Path(args.save_dir).mkdir(parents=True, exist_ok=True)
        vocab.save(str(vocab_path))
        return vocab

    def _save(self, encoder, decoder, vocab, save_dir, epoch, bleu4):
        path = Path(save_dir) / "best_model.pt"
        torch.save({
            "epoch": epoch,
            "bleu4": bleu4,
            "encoder_state": encoder.state_dict(),
            "decoder_state": decoder.state_dict(),
            "encoder_dim": 2048,
            "attention_dim": self.args.attention_dim,
            "embed_dim": self.args.embed_dim,
            "decoder_dim": self.args.decoder_dim,
            "vocab_size": len(vocab),
        }, path)
        logger.info(f"Saved best model → {path} (BLEU-4: {bleu4:.4f})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser("Image Caption Generator — Training")
    p.add_argument("--images_dir", required=True)
    p.add_argument("--captions_file", required=True)
    p.add_argument("--val_captions_file", default=None)
    p.add_argument("--save_dir", default="./weights")
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch_size", type=int, default=32)
    p.add_argument("--embed_dim", type=int, default=256)
    p.add_argument("--attention_dim", type=int, default=256)
    p.add_argument("--decoder_dim", type=int, default=512)
    p.add_argument("--dropout", type=float, default=0.5)
    p.add_argument("--decoder_lr", type=float, default=4e-4)
    p.add_argument("--encoder_lr", type=float, default=1e-4)
    p.add_argument("--fine_tune_encoder", action="store_true")
    p.add_argument("--max_len", type=int, default=50)
    p.add_argument("--freq_threshold", type=int, default=5)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    Trainer(args).run()
