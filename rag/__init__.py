"""
RAG Module
Contains vector database retrieval and context generation.
"""

from .retriever import retrieve_context
from .build_vector_db import update_vector_db

__all__ = [
    'retrieve_context',
    'update_vector_db',
]
