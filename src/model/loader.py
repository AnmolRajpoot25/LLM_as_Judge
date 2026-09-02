import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig


class ModelLoader:

    def __init__(self, model_name):
        self.model_name = model_name

    def load(self):

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )

        tokenizer = AutoTokenizer.from_pretrained(
            self.model_name
        )

        model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.float16
        )

        return tokenizer, model