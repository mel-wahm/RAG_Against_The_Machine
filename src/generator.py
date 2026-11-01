import json
from pathlib import Path
from typing import Any
import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer
from src.models import (
    MinimalSource,
    StudentSearchResults,
    StudentSearchResultsAndAnswer,
    MinimalAnswer,
)


class LLM:
    def __init__(self) -> None:
        self.model: Any = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen3-0.6B",
            dtype=torch.bfloat16
        )
        self.tokenizer: Any = AutoTokenizer.from_pretrained(
            "Qwen/Qwen3-0.6B"
        )

    def prepare_prompt(
        self, query: str, context: list[MinimalSource]
    ) -> str:
        snippets: list[str] = []
        for chunk in context:
            text = Path(chunk.file_path).read_text()[
                chunk.first_character_index:chunk.last_character_index
            ].strip()
            if text:
                snippets.append(text)

        context_str = "\n\n".join(snippets)
        return f"Context:\n{context_str}\n\nQuestion: {query}"

    def answer_a_question(self, query: str) -> str:
        system_instruction = (
            "Answer the question directly and concisely in 1 to 2 "
            "sentences using only the context. Do not repeat the "
            "question or add code blocks unless requested."
        )
        message = self.tokenizer.apply_chat_template(
            [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": query},
            ],
            add_generation_prompt=True,
            tokenize=False,
            enable_thinking=False,
        )
        input_ids = self.tokenizer(message, return_tensors="pt")
        prompt_length = input_ids["input_ids"].shape[1]

        with torch.inference_mode():
            output_ids = self.model.generate(
                input_ids["input_ids"], max_new_tokens=80
            )

        answer: str = self.tokenizer.decode(
            output_ids[0][prompt_length:], skip_special_tokens=True
        ).strip()
        return answer

    def answer_dataset(
        self, student_search_results_path: str, save_directory: str
    ) -> None:
        with open(student_search_results_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        student_search = StudentSearchResults.model_validate(data)

        answers: list[MinimalAnswer] = []
        for result in tqdm(
            student_search.search_results, desc="Generating answers"
        ):
            context_chunks = result.retrieved_sources[:1]
            prompt = self.prepare_prompt(result.question, context_chunks)
            ans_text = self.answer_a_question(prompt)
            answers.append(
                MinimalAnswer(
                    question_id=result.question_id,
                    question=result.question,
                    retrieved_sources=result.retrieved_sources,
                    answer=ans_text,
                )
            )

        final_results = StudentSearchResultsAndAnswer(
            search_results=answers,
            k=student_search.k,
        )

        out_dir = Path(save_directory)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / Path(student_search_results_path).name
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(final_results.model_dump_json(indent=4))
