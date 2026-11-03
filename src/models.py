"""Pydantic data models for the RAG pipeline."""

import uuid
from typing import List
from pydantic import BaseModel, Field


class MinimalSource(BaseModel):
    """Represents a single source of information."""

    file_path: str
    first_character_index: int
    last_character_index: int


class UnansweredQuestion(BaseModel):
    """Represents an unanswered question."""

    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str


class AnsweredQuestion(UnansweredQuestion):
    """Represents an answered question with sources."""

    sources: List[MinimalSource]
    answer: str


class RagDataset(BaseModel):
    """Represents a dataset of RAG questions."""

    rag_questions: List[AnsweredQuestion | UnansweredQuestion]


class MinimalSearchResults(BaseModel):
    """Represents the search results for a single question."""

    question_id: str
    question: str
    retrieved_sources: List[MinimalSource]


class MinimalAnswer(MinimalSearchResults):
    """Represents a search result with an answer."""

    answer: str


class StudentSearchResults(BaseModel):
    """Represents search results for a dataset of questions."""

    search_results: List[MinimalSearchResults]
    k: int


class StudentSearchResultsAndAnswer(BaseModel):
    """Represents search results with answers for a dataset of questions."""

    search_results: List[MinimalAnswer]
    k: int
