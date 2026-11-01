from src.models import MinimalSource
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from pathlib import Path

class LLM:
    def __init__(self):
        self.model = AutoModelForCausalLM.\
            from_pretrained("Qwen/Qwen3-0.6B",
                            dtype=torch.bfloat16)
        self.tokenizer = AutoTokenizer.\
            from_pretrained("Qwen/Qwen3-0.6B")

    def prepare_prompt(self, query: str, context: list[MinimalSource]) -> str:
        prompt = ""
        for chunk in context:
            prompt += Path(chunk.file_path).read_text()[
                chunk.first_character_index : chunk.last_character_index
            ]
        return(prompt + query)

    def answer_a_question(self, query: str) -> None:
        message = self.tokenizer.apply_chat_template(
            [
                {"role": "system", "content": "Answer the question directly and concisely in 1 to 2 sentences" \
                    " using only the context. Do not repeat the question or add code blocks unless requested."},
                {"role": "user", "content": query}
            ],
            tokenize=False, add_generation_prompt=True,
            enable_thinking=False
        )
        input_ids = self.tokenizer(message, return_tensors="pt")
        output_ids = self.model.generate(input_ids["input_ids"], max_new_tokens=45)
        query_length = input_ids["input_ids"].shape[1]
        answer = self.tokenizer.decode(output_ids[0][query_length:]\
                                       , skip_special_tokens=True)
        print(answer)
