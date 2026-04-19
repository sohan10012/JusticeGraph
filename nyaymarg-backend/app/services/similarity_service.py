"""
app/services/similarity_service.py — TF-IDF cosine similarity search.
"""
from __future__ import annotations

import structlog
from sklearn.metrics.pairwise import cosine_similarity

from app.data.seed import get_registry
from app.ml.pipeline import clean_text
from app.schemas.notification import SimilarCase

logger = structlog.get_logger(__name__)


class SimilarityService:
    """
    Builds a precomputed TF-IDF matrix of the entire df_cases corpus on startup,
    then responds to similarity queries in O(n*d) time.
    """

    def build_index(self) -> None:
        """
        Called once after models load. Vectorises all case texts and stores
        the sparse matrix in the DataRegistry for fast querying.
        """
        registry = get_registry()
        if registry.vectorizer is None:
            logger.warning("similarity.index_skipped", reason="vectorizer not loaded")
            return

        texts = registry.df_cases["clean_text"].fillna("").tolist()
        registry.corpus_vectors = registry.vectorizer.transform(texts)
        logger.info("similarity.index_built", n_cases=len(texts))

    def search(
        self,
        query_text:     str,
        top_n:          int = 5,
        court_filter:   str | None = None,
        outcome_filter: str | None = None,
    ) -> list[SimilarCase]:
        registry = get_registry()
        if registry.corpus_vectors is None or registry.vectorizer is None:
            return []

        cleaned   = clean_text(query_text)
        query_vec = registry.vectorizer.transform([cleaned])
        scores    = cosine_similarity(query_vec, registry.corpus_vectors).flatten()
        top_idx   = scores.argsort()[::-1]

        results: list[SimilarCase] = []
        df = registry.df_cases

        for idx in top_idx:
            if len(results) >= top_n:
                break

            case  = df.iloc[int(idx)]
            score = float(scores[int(idx)])

            # Apply filters
            if court_filter:
                ct = str(case.get("court_type", case.get("court_name", "")))
                if court_filter.lower() not in ct.lower():
                    continue

            outcome_label = "Decided" if int(case["outcome"]) == 1 else "Pending"
            if outcome_filter and outcome_filter.lower() != outcome_label.lower():
                continue

            filing = case.get("filing_date")
            results.append(SimilarCase(
                case_id=str(case["case_id"]),
                case_title=str(case["case_title"]),
                case_type=str(case["case_type"]),
                court_name=str(case["court_name"]),
                state=str(case["state"]),
                outcome_label=outcome_label,
                similarity_score=round(score, 4),
                filing_date=str(filing) if filing else None,
            ))

        return results
