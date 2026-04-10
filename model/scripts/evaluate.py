"""
Evaluate trained caption model using BLEU-1/2/3/4 scores.
"""

import argparse
import logging
import pickle
import sys
from pathlib import Path

import torch
import torchvision.transforms as transforms
from nltk.translate.bleu_score import corpus_bleu, SmoothingFunction
from PIL import Image

# Add parent dir to path so we can import from train.py
sys.path.insert(0, str(Path(__file__).parent))
from train import EncoderCNN, DecoderWithAttention, CaptionGenerator, Vocabulary

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_model(checkpoint_path: str, vocab: Vocabulary,
               device: torch.device) -> CaptionGenerator:
    ckpt = torch.load(checkpoint_path, map_location=device)
    encoder = EncoderCNN()
    decoder = DecoderWithAttention(
        attention_dim=ckpt["attention_dim"],
        embed_dim=ckpt["embed_dim"],
        decoder_dim=ckpt["decoder_dim"],
        vocab_size=ckpt["vocab_size"]
    )
    encoder.load_state_dict(ckpt["encoder_state"])
    decoder.load_state_dict(ckpt["decoder_state"])
    gen = CaptionGenerator(encoder, decoder, vocab, device)
    return gen


def evaluate(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Device: {device}")

    vocab = Vocabulary.load(args.vocab_path)
    generator = load_model(args.model_path, vocab, device)

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    references = []
    hypotheses = []
    smooth = SmoothingFunction().method1

    images_dir = Path(args.images_dir)
    with open(args.captions_file) as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith("image")]

    # Group captions by image
    img_caps: dict[str, list[str]] = {}
    for line in lines:
        parts = line.split(",", 1)
        if len(parts) != 2:
            continue
        img_name, cap = parts
        img_caps.setdefault(img_name.strip(), []).append(cap.strip())

    total = min(args.max_samples, len(img_caps))
    logger.info(f"Evaluating on {total} images...")

    for i, (img_name, caps) in enumerate(list(img_caps.items())[:total]):
        img_path = images_dir / img_name
        if not img_path.exists():
            continue
        try:
            image = Image.open(img_path).convert("RGB")
            caption, _ = generator.generate(image, beam_size=args.beam_size)
            hypotheses.append(caption.split())
            references.append([c.split() for c in caps])
            if (i + 1) % 100 == 0:
                logger.info(f"  {i+1}/{total} processed")
        except Exception as e:
            logger.warning(f"Skipping {img_name}: {e}")

    # Compute BLEU scores
    bleu1 = corpus_bleu(references, hypotheses, weights=(1, 0, 0, 0))
    bleu2 = corpus_bleu(references, hypotheses, weights=(0.5, 0.5, 0, 0))
    bleu3 = corpus_bleu(references, hypotheses, weights=(0.33, 0.33, 0.33, 0))
    bleu4 = corpus_bleu(references, hypotheses, weights=(0.25, 0.25, 0.25, 0.25))

    logger.info("\n" + "="*40)
    logger.info("EVALUATION RESULTS")
    logger.info("="*40)
    logger.info(f"BLEU-1: {bleu1:.4f}  ({bleu1*100:.2f}%)")
    logger.info(f"BLEU-2: {bleu2:.4f}  ({bleu2*100:.2f}%)")
    logger.info(f"BLEU-3: {bleu3:.4f}  ({bleu3*100:.2f}%)")
    logger.info(f"BLEU-4: {bleu4:.4f}  ({bleu4*100:.2f}%)")
    logger.info("="*40)

    return {"bleu1": bleu1, "bleu2": bleu2, "bleu3": bleu3, "bleu4": bleu4}


if __name__ == "__main__":
    p = argparse.ArgumentParser("Evaluate Caption Model — BLEU Score")
    p.add_argument("--model_path", required=True)
    p.add_argument("--vocab_path", required=True)
    p.add_argument("--images_dir", required=True)
    p.add_argument("--captions_file", required=True)
    p.add_argument("--beam_size", type=int, default=3)
    p.add_argument("--max_samples", type=int, default=1000)
    evaluate(p.parse_args())
