"""In-memory cosine similarity retrieval over embedding vectors stored in MongoDB documents."""

from dataclasses import dataclass
from typing import Any

from mtes.mapping.vector_math import cosine_similarity
from mtes.persistence.repositories.base_repository import CollectionRepository

EMBEDDING_VECTOR_FIELD = "embedding"
DEFAULT_TOP_K = 20
BOOTSTRAP_RETRIEVAL_CONSISTENCY_MIN = 0.95

EMBEDDING_BACKED_COLLECTIONS: tuple[str, ...] = (
    "dictionary_terms",
    "candidate_archive",
    "tweet_archive",
)


@dataclass(frozen=True, slots=True)
class RetrievalMatch:
    """Single neighbor ranked by cosine similarity."""

    document_id: str
    similarity: float
    label: str


def parse_embedding_vector(raw: object) -> tuple[float, ...] | None:
    if not isinstance(raw, list) or not raw:
        return None
    try:
        return tuple(float(value) for value in raw)
    except (TypeError, ValueError):
        return None


def build_embedding_corpus(
    documents: list[dict[str, Any]],
    *,
    vector_field: str = EMBEDDING_VECTOR_FIELD,
    id_field: str = "_id",
    label_field: str | None = None,
) -> list[tuple[str, str, tuple[float, ...]]]:
    """Extract (document_id, label, vector) tuples from MongoDB documents."""
    corpus: list[tuple[str, str, tuple[float, ...]]] = []
    for document in documents:
        vector = parse_embedding_vector(document.get(vector_field))
        if vector is None:
            continue
        document_id = str(document.get(id_field, ""))
        if not document_id:
            continue
        if label_field is not None and document.get(label_field) is not None:
            label = str(document[label_field])
        elif document.get("token") is not None:
            label = str(document["token"])
        elif document.get("text") is not None:
            label = str(document["text"])
        else:
            label = document_id
        corpus.append((document_id, label, vector))
    return corpus


class InMemoryCosineRetrieval:
    """Rank neighbors by cosine similarity entirely in application memory."""

    def top_k_neighbors(
        self,
        query_vector: tuple[float, ...],
        corpus: list[tuple[str, str, tuple[float, ...]]],
        *,
        k: int = DEFAULT_TOP_K,
        exclude_ids: frozenset[str] | None = None,
    ) -> tuple[RetrievalMatch, ...]:
        excluded = exclude_ids or frozenset()
        ranked: list[RetrievalMatch] = []
        for document_id, label, vector in corpus:
            if document_id in excluded:
                continue
            similarity = cosine_similarity(query_vector, vector)
            ranked.append(
                RetrievalMatch(document_id=document_id, similarity=similarity, label=label)
            )
        ranked.sort(key=lambda item: (-item.similarity, item.document_id, item.label))
        return tuple(ranked[:k])

    def neighbor_id_ranking(
        self,
        query_vector: tuple[float, ...],
        corpus: list[tuple[str, str, tuple[float, ...]]],
        *,
        k: int = DEFAULT_TOP_K,
    ) -> tuple[str, ...]:
        matches = self.top_k_neighbors(query_vector, corpus, k=k)
        return tuple(match.document_id for match in matches)

    def retrieval_consistency(
        self,
        query_vector: tuple[float, ...],
        corpus: list[tuple[str, str, tuple[float, ...]]],
        *,
        k: int = DEFAULT_TOP_K,
        run_count: int = 3,
    ) -> float:
        """Bootstrap §8.2: fraction of runs with identical top-k neighbor id ranking."""
        if run_count < 1:
            return 0.0
        rankings = [
            self.neighbor_id_ranking(query_vector, corpus, k=k) for _ in range(run_count)
        ]
        reference = rankings[0]
        stable_runs = sum(1 for ranking in rankings if ranking == reference)
        return stable_runs / len(rankings)


async def load_embedding_corpus_from_repository(
    repository: CollectionRepository,
    *,
    query: dict[str, Any] | None = None,
    limit: int = 10_000,
    vector_field: str = EMBEDDING_VECTOR_FIELD,
    label_field: str | None = None,
) -> list[tuple[str, str, tuple[float, ...]]]:
    """Load embeddings from MongoDB and prepare an in-memory retrieval corpus."""
    documents = await repository.find_many(query or {}, limit=limit)
    return build_embedding_corpus(documents, vector_field=vector_field, label_field=label_field)
