import numpy as np

from app.ai.base import AIProvider, EmbedPurpose

# Both OpenAI and Gemini accept at least 100 inputs per embedding request.
BATCH_SIZE = 100


async def embed_texts(provider: AIProvider, texts: list[str], purpose: EmbedPurpose) -> np.ndarray:
    """Embed texts in batches and return an (n, dim) float32 matrix of unit vectors.

    Normalising once here means cosine similarity later is just a dot product.
    """
    vectors: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        vectors.extend(await provider.embed(texts[start : start + BATCH_SIZE], purpose))

    matrix = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms
