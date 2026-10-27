from src.retriever import Retriever
from src.chunker import Chunker
import pickle

chunks = Chunker(2000, "data/raw").chunks

retty = Retriever(chunks, "code_answers.json",
                  questions_file="data/datasets/"
                  "UnansweredQuestions/dataset_code_public.json", k=5)
retty = Retriever(chunks, "docs_answers.json",
                  questions_file="data/datasets/"
                  "UnansweredQuestions/dataset_docs_public.json", k=5)
