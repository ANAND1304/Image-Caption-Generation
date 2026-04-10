"""
Model service — BLIP-powered caption generation.

Priority order:
  1. BLIP (Salesforce/blip-image-captioning-base) — real AI, no training needed
  2. Custom CNN+LSTM weights (if model/weights/best_model.pt exists)
  3. Mock fallback (for offline/no-internet environments)

BLIP is downloaded once (~900MB) and cached by HuggingFace in:
  Windows: C:/Users/<you>/.cache/huggingface/hub/
  Mac/Linux: ~/.cache/huggingface/hub/
"""

import sys
import time
import pickle
from pathlib import Path
from typing import Optional

import torch
from PIL import Image

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# 1. BLIP Caption Generator (Production — Real AI)
# ---------------------------------------------------------------------------
class BLIPCaptionGenerator:
    """
    Uses Salesforce BLIP pretrained model.
    Trained on 129 million image-caption pairs.
    Works accurately on ANY image — faces, objects, scenes, animals.
    No training required.
    """

    MODEL_ID = "Salesforce/blip-image-captioning-base"

    def __init__(self):
        from transformers import BlipProcessor, BlipForConditionalGeneration

        logger.info("Loading BLIP model (first run downloads ~900MB)...")
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self._processor = BlipProcessor.from_pretrained(self.MODEL_ID)
        self._model = BlipForConditionalGeneration.from_pretrained(
            self.MODEL_ID,
            torch_dtype=torch.float16 if self._device.type == "cuda" else torch.float32,
        ).to(self._device)
        self._model.eval()

        logger.info("BLIP model loaded successfully", device=str(self._device))

    def generate(self, image: Image.Image, beam_size: int = 3) -> tuple[str, float]:
        """
        Generate caption using BLIP with beam search.
        Returns: (caption_string, confidence_score)
        """
        # Ensure RGB
        image = image.convert("RGB")

        # Preprocess
        inputs = self._processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=50,
                num_beams=beam_size,
                min_length=5,
                repetition_penalty=1.3,    # avoids repeating words
                length_penalty=1.0,
                early_stopping=True,
            )

        caption = self._processor.decode(output_ids[0], skip_special_tokens=True)

        # BLIP scores: compute a simple proxy confidence from beam scores
        with torch.no_grad():
            scores_output = self._model.generate(
                **inputs,
                max_new_tokens=50,
                num_beams=beam_size,
                output_scores=True,
                return_dict_in_generate=True,
                min_length=5,
                repetition_penalty=1.3,
            )
        # Mean of top token log-probs → normalized confidence
        if hasattr(scores_output, "sequences_scores"):
            raw = float(scores_output.sequences_scores[0].cpu())
            confidence = float(min(0.99, max(0.5, 1.0 + raw / 20.0)))
        else:
            confidence = 0.88  # BLIP default

        return caption.strip(), confidence


# ---------------------------------------------------------------------------
# 2. Custom CNN+LSTM Generator (if weights trained)
# ---------------------------------------------------------------------------
_MODEL_SCRIPTS_DIR = str(
    Path(__file__).parent.parent.parent.parent / "model" / "scripts"
)
if _MODEL_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _MODEL_SCRIPTS_DIR)

try:
    from train import EncoderCNN, DecoderWithAttention, CaptionGenerator, Vocabulary
    _CUSTOM_MODEL_AVAILABLE = True
except ImportError:
    _CUSTOM_MODEL_AVAILABLE = False


class CustomModelGenerator:
    """Wrapper for trained CNN+LSTM model."""

    def __init__(self, model_path: str, vocab_path: str):
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        ckpt = torch.load(model_path, map_location=device)
        with open(vocab_path, "rb") as f:
            vocab = pickle.load(f)
        encoder = EncoderCNN()
        decoder = DecoderWithAttention(
            attention_dim=ckpt["attention_dim"],
            embed_dim=ckpt["embed_dim"],
            decoder_dim=ckpt["decoder_dim"],
            vocab_size=ckpt["vocab_size"],
        )
        encoder.load_state_dict(ckpt["encoder_state"])
        decoder.load_state_dict(ckpt["decoder_state"])
        self._gen = CaptionGenerator(encoder, decoder, vocab, device=device)
        logger.info("Custom CNN+LSTM model loaded", device=str(device))

    def generate(self, image: Image.Image, beam_size: int = 3) -> tuple[str, float]:
        return self._gen.generate(image, beam_size=beam_size)


# ---------------------------------------------------------------------------
# 3. Mock Generator (offline fallback)
# ---------------------------------------------------------------------------
class MockCaptionGenerator:
    """
    Returns deterministic fake captions.
    Used only when BLIP fails to download (no internet).
    """
    CAPTIONS = [
        "a person standing in front of a building",
        "a group of people gathered together outdoors",
        "a man wearing a dark shirt looking at the camera",
        "a woman smiling in a brightly lit room",
        "an object placed on a table indoors",
        "a scenic view with natural surroundings",
        "a close-up of a person's face",
        "a colorful scene with multiple objects visible",
    ]

    def __init__(self):
        logger.info("MockCaptionGenerator initialized (no internet / offline mode)")

    def generate(self, image: Image.Image, beam_size: int = 3) -> tuple[str, float]:
        import hashlib
        img_hash = int(hashlib.md5(image.tobytes()[:500]).hexdigest(), 16)
        caption = self.CAPTIONS[img_hash % len(self.CAPTIONS)]
        time.sleep(0.3)
        return caption, 0.61


# ---------------------------------------------------------------------------
# Main Model Service
# ---------------------------------------------------------------------------
class ModelService:
    """
    Singleton service. Tries to load in this order:
      1. BLIP  (best — works on any image)
      2. Custom CNN+LSTM weights (if trained)
      3. Mock  (offline fallback)
    """

    def __init__(self):
        self._generator = None
        self._loaded = False
        self._mode = "not_loaded"   # "blip" | "custom" | "mock"

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def device_name(self) -> str:
        if torch.cuda.is_available():
            return f"cuda ({torch.cuda.get_device_name(0)})"
        return "cpu"

    @property
    def mode(self) -> str:
        return self._mode

    def load(self) -> None:
        if self._loaded:
            return

        # ── Try BLIP first ──────────────────────────────────────────────
        try:
            self._generator = BLIPCaptionGenerator()
            self._mode = "blip"
            self._loaded = True
            logger.info("Running in BLIP mode — real AI captions active")
            return
        except Exception as e:
            logger.warning("BLIP load failed — trying custom model", error=str(e))

        # ── Try custom CNN+LSTM weights ──────────────────────────────────
        model_path = Path(settings.model_path)
        vocab_path = Path(settings.vocab_path)
        if _CUSTOM_MODEL_AVAILABLE and model_path.exists() and vocab_path.exists():
            try:
                self._generator = CustomModelGenerator(
                    str(model_path), str(vocab_path))
                self._mode = "custom"
                self._loaded = True
                logger.info("Running in custom CNN+LSTM mode")
                return
            except Exception as e:
                logger.warning("Custom model load failed", error=str(e))

        # ── Fallback: Mock ───────────────────────────────────────────────
        self._generator = MockCaptionGenerator()
        self._mode = "mock"
        self._loaded = True
        logger.warning("Running in MOCK mode — install transformers for real AI")

    def generate_caption(self, image: Image.Image, beam_size: int = None) -> dict:
        if not self._loaded:
            self.load()

        beam_size = beam_size or settings.beam_size
        t0 = time.perf_counter()

        caption, confidence = self._generator.generate(image, beam_size=beam_size)

        elapsed_ms = round((time.perf_counter() - t0) * 1000)

        logger.info("Caption generated",
                    caption=caption,
                    confidence=round(confidence, 3),
                    ms=elapsed_ms,
                    mode=self._mode)

        return {
            "caption": caption,
            "confidence": round(confidence, 3),
            "processing_time_ms": elapsed_ms,
            "beam_size": beam_size,
            "model_mode": self._mode,
        }


# Singleton
model_service = ModelService()
