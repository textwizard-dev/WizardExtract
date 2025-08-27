# SPDX-FileCopyrightText: 2024–2025 Mattia Rubino
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations
import os
import time
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache, cached_property
from pathlib import Path
from typing import Dict, List, Literal, Optional
from dataclasses import asdict


try:
    import numpy as _np
    import torch
    from torch.serialization import add_safe_globals

    add_safe_globals([_np.core.multiarray._reconstruct])

    _orig_torch_load = torch.load
    def _torch_load_override(f, *args, **kwargs):
        return _orig_torch_load(f, *args, weights_only=False, **kwargs)
    torch.load = _torch_load_override

except ImportError:
    pass


###############################################################################
#                            DATA STRUCTURES                                  #
###############################################################################

@dataclass(frozen=True, slots=True)
class Entity:
    text: str
    label: str
    start: int
    end: int
    score: Optional[float] = None


@dataclass(frozen=True, slots=True)
class TokenAnalysis:
    text: str
    lemma: str
    upos: str
    xpos: str
    dep: str
    head: int
    ent_type: str
    start: int
    end: int


class EntitiesResult:
    __slots__ = ("_entities", "full_analysis", "_wizard_ner")
    
    def __init__(
        self,
        entities: List[Entity],
        full_analysis: Dict[int, TokenAnalysis],
        _wizard_ner: "WizardNER | None" = None,               
    ):
        grouped: Dict[str, List[Entity]] = {}
        for ent in entities:
            grouped.setdefault(ent.label, []).append(ent)
        self._entities = grouped
        self.full_analysis = full_analysis
        self._wizard_ner = _wizard_ner 

    # access helpers
    @property
    def entities(self):
        return self._entities

    @property
    def labels(self):
        return list(self._entities.keys())

    @property
    def counts(self):
        return {lbl: len(lst) for lbl, lst in self._entities.items()}

    def to_dicts(self):
        return [asdict(e) for lst in self._entities.values() for e in lst]

    def most_common(self, n: int = 5):
        all_txt = [e.text for lst in self._entities.values() for e in lst]
        top = [t for t, _ in Counter(all_txt).most_common(n)]
        return [next(e for lst in self._entities.values() for e in lst if e.text == t) for t in top]

    def get(self, label: str):
        return self._entities.get(label, [])

    def __getitem__(self, label: str):
        return self._entities[label]

    def __iter__(self):
        return iter(self._entities.items())

    def __len__(self):
        return sum(len(v) for v in self._entities.values())

###############################################################################
#                                ENGINE                                       #
###############################################################################

Device = Literal["auto", "cpu", "gpu"]

class WizardNER:
    SUPPORTED_ENGINES = ("spacy", "stanza", "spacy_stanza")

    def __init__(self, engine: Literal["spacy", "stanza", "spacy_stanza"], model: str, language: str, device: Device = "auto"):
        if engine not in self.SUPPORTED_ENGINES:
            raise ValueError(f"Unsupported engine '{engine}'.")
        if device not in {"auto", "cpu", "gpu"}:
            raise ValueError("device must be 'auto', 'cpu' or 'gpu'.")
        if device == "gpu" and not self._gpu_available():
            raise RuntimeError("GPU requested but not available.")

        self.engine = engine
        self.model = model
        self.language = language
        self.device = device

    # ------------------------------------------------------------------
    # GPU helper
    # ------------------------------------------------------------------
    @staticmethod
    def _gpu_available() -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    # ------------------------------------------------------------------
    # Model loaders (cached)
    # ------------------------------------------------------------------
    @staticmethod
    @lru_cache(maxsize=None)
    def _load_spacy_model(model: str, use_gpu: bool):
        try:
            import spacy
            if use_gpu:
                spacy.require_gpu()
        except ImportError as e:
            raise RuntimeError(
                "spaCy not installed. Install with `pip install textwizard[ner]`."
            ) from e

        nlp_path = Path(model) if Path(model).exists() else model
        try:
            return spacy.load(nlp_path)
        except OSError as e:
            if os.getenv("TW_NO_MODEL_DOWNLOAD"):
                raise RuntimeError(
                    f"spaCy model '{model}' not found and auto-download disabled."
                ) from e
            from spacy.cli import download as spacy_download
            spacy_download(model)
            return spacy.load(nlp_path)

    @staticmethod
    @lru_cache(maxsize=None)
    def _load_stanza_pipeline(language: str, use_gpu: bool):
        try:
            import stanza
        except ImportError as e:
            raise RuntimeError(
                "Stanza not installed. Install with `pip install textwizard[ner]`"
            ) from e

        try:
            return stanza.Pipeline(
                lang=language,
                processors="tokenize,ner",
                use_gpu=use_gpu,
                verbose=False,
            )
        except Exception as e:
            if os.getenv("TW_NO_MODEL_DOWNLOAD"):
                raise RuntimeError(
                    f"Stanza model for '{language}' not found and auto-download disabled."
                ) from e

        stanza.download(language, processors="tokenize,ner", verbose=False)
        return stanza.Pipeline(
            lang=language,
            processors="tokenize,ner",
            use_gpu=use_gpu,
            verbose=False,
        )


    @staticmethod
    @lru_cache(maxsize=None)
    def _load_spacy_stanza_pipeline(language: str, use_gpu: bool):
        try:
            import spacy_stanza
            if use_gpu:
                spacy_stanza.require_gpu()
        except ImportError as e:
            raise RuntimeError(
                "spacy-stanza not installed. Install with `pip install textwizard[ner]`."
            ) from e

        try:
            return spacy_stanza.load_pipeline(language, processors="tokenize,ner", verbose=False)
        except Exception as e: 
            if os.getenv("TW_NO_MODEL_DOWNLOAD"):
                raise RuntimeError(
                    f"Stanza model for '{language}' is missing and auto-download."
                    "is disabled (TW_NO_MODEL_DOWNLOAD=1)."
                ) from e

        spacy_stanza.download(language, verbose=False)
        return spacy_stanza.load_pipeline(language, processors="tokenize,ner",verbose=False)

    # ------------------------------------------------------------------
    # Lazy NLP pipeline per instance
    # ------------------------------------------------------------------
    @cached_property
    def _nlp(self):
        want_gpu = {
            "cpu": False,
            "gpu": True,
            "auto": self._gpu_available(),
        }[self.device]

        if self.engine == "spacy":
            return self._load_spacy_model(self.model, want_gpu)
        if self.engine == "stanza":
            return self._load_stanza_pipeline(self.language, want_gpu)
        return self._load_spacy_stanza_pipeline(self.language, want_gpu)

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def run(self, text: str) -> EntitiesResult:
        ents: List[Entity] = []
        tokens: Dict[int, TokenAnalysis] = {}

        if self.engine in ("spacy", "spacy_stanza"):
            doc = self._nlp(text)
            for i, tok in enumerate(doc):
                tokens[i] = TokenAnalysis(tok.text, tok.lemma_, tok.pos_, tok.tag_, tok.dep_, tok.head.i, tok.ent_type_, tok.idx, tok.idx + len(tok))
            ents.extend(Entity(e.text, e.label_, e.start_char, e.end_char) for e in doc.ents)

        else: 
            doc = self._nlp(text)
            idx = 0

            for sent in doc.sentences:
                for token in sent.tokens:
                    w = token.words[0]
                    tokens[idx] = TokenAnalysis(
                        text=token.text,
                        lemma=w.lemma,
                        upos=w.upos,
                        xpos=w.xpos,
                        dep=w.deprel,
                        head=w.head,
                        ent_type=getattr(w, "ner", ""),
                        start=token.start_char,
                        end=token.end_char,
                    )
                    idx += 1

                for ent in sent.ents:
                    ents.append(
                        Entity(
                            text=ent.text,
                            label=ent.type,
                            start=ent.start_char,
                            end=ent.end_char,
                        )
                    )

        return EntitiesResult(ents, tokens)

    # ------------------------------------------------------------------
    # Benchmark helper
    # ------------------------------------------------------------------
    def benchmark(self, text: str, n: int = 100, warmup: int = 3):
        for _ in range(warmup):
            _ = self.run(text)
        t0 = time.perf_counter()
        for _ in range(n):
            _ = self.run(text)
        t = time.perf_counter() - t0
        return {"docs": n, "total_sec": t, "docs_per_sec": n / t if t else 0.0, "ms_per_doc": (t / n) * 1000}

