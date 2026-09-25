import math
from processing.schemas import ProcessedJob
from typing import Optional, Protocol, Sequence
EMBEDDING_DIM = 384
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


EMBEDDING_RECIPE_VERSION = 1

class Encoder(Protocol):
    def encode(self, texts: Sequence[str])-> Sequence[Sequence[float]]: ...

def _format_experience(job: ProcessedJob) -> Optional[str]:
    lo, hi = job.experience_min_years,job.experience_max_years
    if lo is None and hi is None:
        return None
    if lo is not None and hi is not None:
        return f"{lo}-{hi} years"
    if lo is not None:
        return f"{lo}+ years"
    return f"up to {hi} years"


def build_embedding_text(job: ProcessedJob) -> str:
    """Pure. Compose a compact canonical string from structured fields ONLY.

    ⚠️ This recipe MUST be identical on the user side later, or job and user
    vectors won't be comparable. Keep it deterministic; skip empty fields.
    """

    parts: list[str]= []

    if job.role:
        parts.append(f"Role: {job.role}")
    parts.append(f"Seniority: {job.seniority.value}")
    if job.skills:
        parts.append(f"Skills: {', '.join(job.skills)}")
    if job.nice_to_have_skills:
        parts.append(f"Nice to have: {', '.join(job.nice_to_have_skills)}")
    if job.domain:
        parts.append(f"Domain: {job.domain}")
    parts.append(f"Employment: {job.employment_type.value}")
    parts.append(f"Remote: {job.remote.value}")
    parts.append(f"Education: {job.education.value}")
    exp = _format_experience(job)
    if exp:
        parts.append(f"Experience: {exp}")
    if job.responsibilities:
        parts.append("Responsibilities: " + "; ".join(job.responsibilities))
    return "\n".join(parts)



class JobEmbedder:
    def __init__(self, encoder: Encoder, dim: int = EMBEDDING_DIM):
        self._encoder = encoder 
        self._dim = dim
    
    def embed(self, job: ProcessedJob)-> list[float]:
        return self.embed_many([job])[0]

    def _validate(self, vector) -> list[float]:
        vec = [float(x) for x in vector]
        if len(vec) != self._dim:
            raise ValueError(f"expected {self._dim} - dim vector, got {len(vec)}")
        if not all(math.isfinite(x) for x in vec) or not any(vec):
            raise ValueError("embedding must be finite and nonzero")
        return vec
    def embed_many(self,jobs:Sequence[ProcessedJob])-> list[list[float]]:
        if not jobs:
            return []
        texts= [build_embedding_text(j) for j in jobs]
        vectors = list(self._encoder.encode(texts))
        if len(vectors) != len(texts):
            raise ValueError("encoder returned the wrong number of vectors")
        return [self._validate(v) for v in vectors]

class FastEmbedEncoder:
    """Production encoder. Lazy-imports fastembed so the module (and its
    tests) load without the dependency present."""
    def __init__(self,model_name: str = EMBEDDING_MODEL):
        from fastembed import TextEmbedding
        self._model = TextEmbedding(model_name = model_name)
    def encode(self,texts:Sequence[str])-> list[list[float]]:
        return [list(v) for v in self._model.embed(list(texts))]
    

