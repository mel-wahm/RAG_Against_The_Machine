from rich import print
import json
from pathlib import Path
from tqdm import tqdm
from src.models import (
    MinimalSource,
    StudentSearchResults,
    StudentSearchResultsAndAnswer,
    MinimalAnswer,
)


class LLM:
    def __init__(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.model: AutoModelForCausalLM = \
            AutoModelForCausalLM.from_pretrained(
                "Qwen/Qwen3-0.6B", dtype=torch.bfloat16
            )
        self.tokenizer: AutoTokenizer = \
            AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")

    def prepare_prompt(self, query: str, context: list[MinimalSource]) -> str:
        chunks: list[str] = []
        for chunk in context:
            text = chunk.file_path + "\n" + (
                Path(chunk.file_path)
                .read_text()[
                    chunk.first_character_index: chunk.last_character_index
                ]
                .strip()
            )
            if text:
                chunks.append(text)

        context_str = "\n\n---> ".join(chunks)
        return f"Context:\n{context_str}\n\nQuestion: {query}"

    def answer_batch(self, batch: list[str],
                     context: list[list[MinimalSource]]) -> list[str]:
        augm_batch = []
        system_instruction = (
            "Answer the question directly and concisely in 1 to 2 "
            "sentences using only the context. Do not repeat the "
            "question or add code blocks unless requested."
        )
        for mix in zip(batch, context):
            augm_batch.append(self.prepare_prompt(mix[0], mix[1]))
        self.tokenizer.padding_side = "left"
        questions = self.tokenizer.apply_chat_template(
            [
                [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ] for prompt in augm_batch
            ],
            padding=True,
            tokenize=True,
            add_generation_prompt=True,
            enable_thinking=False,
            return_tensors="pt"
        )
        length = questions["input_ids"].shape[1]
        answers = self.model.generate(**questions, max_new_tokens=180)
        ret = []
        for answer in answers:
            ret.append(self.tokenizer.decode(answer[length:],
                                             skip_special_tokens=True))

        return ret

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
        output_ids = self.model.generate(
            input_ids["input_ids"], max_new_tokens=180,
                    )

        answer: str = self.tokenizer.decode(
            output_ids[0][prompt_length:], skip_special_tokens=True
        ).strip()
        return answer

    def answer_dataset(
        self, student_search_results_path: str, save_directory: str
    ) -> None:
        path = Path(student_search_results_path)
        if not path.is_file():
            print(
                f"Error: Search results file "
                f"'{student_search_results_path}' not found."
            )
            return

        try:
            with open(path) as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(
                f"Error: File '{student_search_results_path}' "
                "contains invalid JSON."
            )
            return
        except Exception as e:
            print(f"Error reading '{student_search_results_path}': {e}")
            return

        try:
            search_results = StudentSearchResults.model_validate(data)
        except Exception as e:
            print(f"Error: Invalid student search results format: {e}")
            return

        returns = []
        for idx in tqdm(range(0, len(search_results.search_results), 4),
                        desc="Answering the dataset questions",):
            searches = search_results.search_results
            queries = []
            contexts = []
            for search in searches[idx:idx + 4]:
                queries.append(search.question)
                contexts.append(search.retrieved_sources[:1])

            answers = self.answer_batch(queries, contexts)

            for n, search in enumerate(searches[idx:idx + 4]):
                answer = answers[n]
                returns.append(
                    MinimalAnswer(
                        question_id=search.question_id,
                        question=search.question,
                        retrieved_sources=search.retrieved_sources,
                        answer=answer,
                    )
                )
        final_result = StudentSearchResultsAndAnswer(
            search_results=returns, k=search_results.k
        )
        path_name = path.name
        save_dir = Path(save_directory)
        try:
            save_dir.mkdir(parents=True, exist_ok=True)
            save_file = save_dir / path_name
            with open(save_file, "w") as f:
                f.write(final_result.model_dump_json(indent=4))
        except Exception as e:
            print(f"Error saving answers to '{save_directory}': {e}")
