# 🧠 WiseSpeak: LoRA Fine-Tune for Elder-Friendly Explanations
*Base Model: `google/flan-t5-base` | Adapter: `lora_core_finetune`*

WiseSpeak is a lightweight LoRA adapter fine-tuned on *short + simplified* explanation pairs, tailored for elderly and non-technical users. The model produces clear, reassuring, and readable answers, ideal for everyday tech and wellness questions.

---

## 📊 Performance Highlights (ELDER-X Metric)

| Metric         | Baseline (FLAN-T5) | WiseSpeak LoRA | Improvement |
|----------------|--------------------|----------------|-------------|
| Readability    | 54.1               | **85.3**       | +31.2       |
| Simplicity     | 49.2               | **34.8**       | —14.4       |
| Actionability  | 4.0                | **4.3**        | ≈0          |
| Comfort        | 1.1                | **2.3**        | +1.2        |
| **ELDER-X**    | **43.8**           | **56.0**       | **+12.2**   |

> **Conclusion**: Short + Simplify is the most effective and balanced mode for everyday use.

---

## 🚀 How to Use

### 🔌 Load with PEFT (adapter only)

```python
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from peft import PeftModel

base_model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base", device_map="auto")
tokenizer  = AutoTokenizer.from_pretrained("google/flan-t5-base")

model = PeftModel.from_pretrained(base_model, "./lora_core_finetune")

prompt = "Why isn't my phone charging?"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=120)

print(tokenizer.decode(outputs[0], skip_special_tokens=True))
