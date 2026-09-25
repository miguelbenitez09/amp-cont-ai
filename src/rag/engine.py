"""
Retrieval-Augmented Generation (RAG) Engine for Panamanian Maritime Knowledge.
Performs semantic vector search across Panamanian maritime regulations, port concessions,
and MLOps architectural references.

Author: Desarrollado v1.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import math
import re
from typing import Any, Dict, List, Optional
from src.rag.knowledge_base import MARITIME_LEGAL_DOCUMENTS


class MaritimeRAGEngine:
    """
    Lightweight, deterministic vector retrieval engine.
    Computes TF-IDF vector embeddings with cosine similarity scoring
    over curated Panamanian maritime legal texts and MLOps doctrine.
    """

    def __init__(self, documents: Optional[List[Dict[str, str]]] = None):
        self.documents = documents or MARITIME_LEGAL_DOCUMENTS
        self.vocabulary: Dict[str, int] = {}
        self.doc_vectors: List[Dict[str, float]] = []
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r"\b[a-zA-ZáéíóúÁÉÍÓÚñÑ0-9_]{3,}\b", text.lower())
        stopwords = {
            "para", "como", "este", "esta", "estos", "estas", "sobre", "entre",
            "todos", "todas", "pero", "porque", "cuando", "donde", "quien",
            "the", "and", "for", "with", "from", "that", "this"
        }
        return [w for w in words if w not in stopwords]

    def _build_index(self) -> None:
        doc_count = len(self.documents)
        df_counts: Dict[str, int] = {}

        # 1. Term frequency per doc and doc frequency
        tokenized_docs = []
        for doc in self.documents:
            tokens = self._tokenize(doc["title"] + " " + doc["content"])
            tokenized_docs.append(tokens)
            unique_terms = set(tokens)
            for t in unique_terms:
                df_counts[t] = df_counts.get(t, 0) + 1

        # 2. Compute IDF & TF-IDF vectors
        self.doc_vectors = []
        for tokens in tokenized_docs:
            tf: Dict[str, float] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0.0) + 1.0

            vec: Dict[str, float] = {}
            norm_sq = 0.0
            for t, freq in tf.items():
                idf = math.log((doc_count + 1) / (df_counts.get(t, 1) + 1)) + 1.0
                weight = freq * idf
                vec[t] = weight
                norm_sq += weight * weight

            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            # Normalize vector to unit length
            norm_vec = {t: w / norm for t, w in vec.items()}
            self.doc_vectors.append(norm_vec)

    def query(self, query_text: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Executes semantic retrieval for a natural language question.
        Returns top matching documents, similarity scores, and synthesized answer.
        """
        q_tokens = self._tokenize(query_text)
        if not q_tokens:
            return {
                "query": query_text,
                "matches": [],
                "synthesized_response": "Consulta vacía o sin términos clave significativos.",
                "author": "Desarrollado v1.0 Miguel Benítez"
            }

        q_tf: Dict[str, float] = {}
        for t in q_tokens:
            q_tf[t] = q_tf.get(t, 0.0) + 1.0

        q_norm_sq = sum(v * v for v in q_tf.values())
        q_norm = math.sqrt(q_norm_sq) if q_norm_sq > 0 else 1.0

        scores: List[tuple[int, float]] = []
        for idx, doc_vec in enumerate(self.doc_vectors):
            dot_product = sum(doc_vec.get(t, 0.0) * (q_tf[t] / q_norm) for t in q_tokens)
            scores.append((idx, dot_product))

        # Sort descending by similarity
        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scores[:top_k]:
            if score > 0.01:
                doc = self.documents[idx]
                results.append({
                    "id": doc["id"],
                    "title": doc["title"],
                    "citation": doc["citation"],
                    "relevance_score": round(float(score), 4),
                    "excerpt": doc["content"][:280] + "..."
                })

        # Synthesize context-grounded response
        if results:
            top_match = results[0]
            answer = (
                f"Con base en la normativa panameña y la documentación técnica ({top_match['citation']}): "
                f"{self.documents[scores[0][0]]['content']}"
            )
        else:
            answer = (
                "No se encontraron referencias específicas de alta correlación en el corpus de leyes "
                "marítimas de Panamá ni en el manual MLOps para la consulta ingresada."
            )

        return {
            "query": query_text,
            "total_documents_searched": len(self.documents),
            "matches_retrieved": len(results),
            "top_matches": results,
            "synthesized_response": answer,
            "author": "Desarrollado v1.0 Miguel Benítez"
        }
