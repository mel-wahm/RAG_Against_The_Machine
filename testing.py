from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen3-0.6B"

model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer : AutoTokenizer = AutoTokenizer.from_pretrained(model_name)

tokenizer.padding_side = "left"
message1 = "What is the capital of France?"
message2 = "please tell me, what is the sum of 2 and 5"
message3 = "name three programming languages"

full_prompt = tokenizer.apply_chat_template(
    [
        [{"role": "system", "content": "You are an agent that is supposed to answer questions"},
        {"role": "user", "content": message1}],
        [{"role": "system", "content": "You are an agent that is supposed to answer questions"},
        {"role": "user", "content": message2}],
        [{"role": "system", "content": "You are an agent that is supposed to answer questions"},
        {"role": "user", "content": message3}],
    ],
    padding=True,
    tokenize=True,
    add_generation_prompt=True,
    enable_thinking=False,
    return_tensors="pt"
)

from rich import print

attention_mask = full_prompt["attention_mask"]
answer = model.generate(**full_prompt,
                        max_new_tokens=180)
length = full_prompt["input_ids"].shape[1]
for idx, ans in enumerate(answer):
    print(tokenizer.decode(ans[length:], skip_special_tokens=True))
    print("*" * 50, "\n\n")
# prompt_length = full_prompt["input_ids"].shape[1]
# print(prompt_length)

