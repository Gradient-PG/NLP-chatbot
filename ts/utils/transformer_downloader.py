from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
from pathlib import Path
import os

if __name__ == "__main__":
    modelpath = Path('ts/models/DialoGPT-medium')
    config = AutoConfig.from_pretrained("microsoft/DialoGPT-medium")
    model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium", config=config)
    tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
    try:
        os.mkdir(modelpath.as_posix())
    except OSError:
        print (f"Creation of directory {modelpath.as_posix()} failed")
        print("Assuming the model is already downloaded")
    else:
        print (f"Successfully created directory {modelpath.as_posix()} ")
        model.save_pretrained(modelpath.as_posix())
        tokenizer.save_pretrained(modelpath.as_posix())
