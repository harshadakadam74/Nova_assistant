"""Voice verification for authorized-user access.

This module prefers Resemblyzer when installed for real speaker embeddings,
and falls back to a lightweight deterministic fingerprint when it is not.
The goal is to keep the application usable without the extra model package,
while still providing a consistent voice-lock mechanism.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import numpy as np

try:
    from resemblyzer import VoiceEncoder
except ImportError:  # pragma: no cover - optional dependency
    VoiceEncoder = None


class VoiceAuthenticator:
    """Store and compare a single voiceprint for the authorized user."""

    def __init__(self, voiceprint_path: str | None = None, threshold: float = 0.75):
        self.threshold = threshold
        self.voiceprint_path = Path(
            voiceprint_path or os.path.join(os.path.dirname(__file__), "..", "data", "voiceprint.npy")
        )
        self.voiceprint_path.parent.mkdir(parents=True, exist_ok=True)

        self._encoder = None
        if VoiceEncoder is not None:
            try:
                self._encoder = VoiceEncoder("cpu")
            except Exception:
                self._encoder = None

    def _to_float32(self, samples):
        if samples is None:
            return None
        arr = np.asarray(samples, dtype=np.float32)
        if arr.size == 0:
            return None
        arr = arr.astype(np.float32, copy=False)
        if arr.ndim != 1:
            arr = arr.reshape(-1)
        return arr

    def _fallback_embedding(self, samples: np.ndarray) -> np.ndarray:
        arr = self._to_float32(samples)
        if arr is None:
            return np.zeros(64, dtype=np.float32)

        frame_size = 1024
        hop = 512
        features = []

        for i in range(0, max(1, len(arr) - frame_size), hop):
            frame = arr[i : i + frame_size]
            if len(frame) < frame_size:
                break
            window = frame * np.hanning(frame_size)
            spectrum = np.abs(np.fft.rfft(window))
            spectrum = spectrum[:64]
            features.append(spectrum)

        if not features:
            return np.zeros(64, dtype=np.float32)

        embedding = np.mean(np.vstack(features), axis=0)
        embedding = embedding.astype(np.float32)

        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding

    def _encode_samples(self, samples):
        arr = self._to_float32(samples)
        if arr is None:
            return None

        if self._encoder is not None:
            try:
                embedding = self._encoder.embed_utterance(arr)
                if embedding is not None:
                    emb = np.asarray(embedding, dtype=np.float32).reshape(-1)
                    norm = np.linalg.norm(emb)
                    if norm > 0:
                        emb = emb / norm
                    return emb
            except Exception:
                pass

        return self._fallback_embedding(arr)

    def save_voiceprint(self, samples):
        recordings = samples if isinstance(samples, (list, tuple)) else [samples]
        embeddings = [
            embedding
            for recording in recordings
            if (embedding := self._encode_samples(recording)) is not None
        ]
        if not embeddings:
            raise ValueError("No valid audio samples received for voice enrollment.")
        embedding = np.mean(np.stack(embeddings), axis=0)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        np.save(self.voiceprint_path, embedding.astype(np.float32))
        return embedding

    def load_voiceprint(self):
        if not self.voiceprint_path.exists():
            return None
        try:
            emb = np.load(self.voiceprint_path)
            emb = np.asarray(emb, dtype=np.float32).reshape(-1)
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            return emb
        except Exception:
            return None

    def verify(self, samples) -> bool:
        """Return True only when an authorized voiceprint exists and matches."""
        if samples is None:
            return False

        if not self.is_enrolled():
            return False

        stored = self.load_voiceprint()
        if stored is None:
            return False

        current = self._encode_samples(samples)
        if current is None:
            return False

        similarity = float(np.dot(stored, current))
        return similarity >= self.threshold

    def is_enrolled(self) -> bool:
        return self.voiceprint_path.exists()
