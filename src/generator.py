from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class LLM:
    def __init__(self):
        self.model = AutoModelForCausalLM.\
            from_pretrained("Qwen/Qwen3-0.6B", dtype=torch.bfloat16)
        self.tokenizer = AutoTokenizer.\
            from_pretrained("Qwen/Qwen3-0.6B")

    def answer_a_question(self, query: str) -> None:
        input_ids = self.tokenizer(query, return_tensors="pt")
        output_ids = self.model.generate(input_ids["input_ids"], max_new_tokens=60)
        query_length = len(query)
        answer = self.tokenizer.decode(output_ids, skip_special_tokens=True)\
            [0][query_length:]
        print(answer)

llm = LLM()
llm.answer_a_question("the colour of the sky is ")