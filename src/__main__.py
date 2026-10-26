from src.retriever import Retriever
import pickle

with open("chunks.pkl", "rb") as f:
    chunks = pickle.load(f)

retty = Retriever(chunks, "code_answers.json",
                  questions_file="data/datasets/"
                  "UnansweredQuestions/dataset_code_public.json", k=5)
retty = Retriever(chunks, "docs_answers.json",
                  questions_file="data/datasets/"
                  "UnansweredQuestions/dataset_docs_public.json", k=5)
