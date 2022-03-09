import torch
import os
import logging
import json
from abc import ABC

from ts.torch_handler.base_handler import BaseHandler
from transformers import AutoTokenizer, AutoModel, MarianMTModel, MarianTokenizer

logger = logging.getLogger(__name__)


class TranslationHandler(BaseHandler, ABC):

    def __init__(self):
        super(TranslationHandler, self).__init__()
        self.initialized = False
        self._LANG_MAP = {
            "pl": "Polish",
            "pol": "Polish",
            "en": "English",
            "eng": "English"
        }

    def initialize(self, ctx):
        self.manifest = ctx.manifest
        properties = ctx.system_properties
        model_dir = properties.get("model_dir")
        serialized_file = self.manifest["model"]["serializedFile"]
        model_pt_path = os.path.join(model_dir, serialized_file)
        self.device = torch.device(
            "cuda:" + str(properties.get("gpu_id"))
            if torch.cuda.is_available() and properties.get("gpu_id") is not None
            else "cpu"
        )
        # self.device = "cpu"
        # read configs for the mode, model_name, etc. from setup_config.json
        setup_config_path = os.path.join(model_dir, "setup_config.json")
        if os.path.isfile(setup_config_path):
            with open(setup_config_path) as setup_config_file:
                self.setup_config = json.load(setup_config_file)
        else:
            logger.warning("Missing the setup_config.json file.")
        # Loading the model and tokenizer from checkpoint and config files based on the user's choice of mode
        # further setup config can be added.
        self.tokenizer = MarianTokenizer.from_pretrained(model_dir)
        if self.setup_config["save_mode"] == "torchscript":
            self.model = torch.jit.load(model_pt_path)
        elif self.setup_config["save_mode"] == "pretrained":
            self.model = MarianMTModel.from_pretrained(model_dir)
        else:
            logger.warning("Missing the checkpoint or state_dict.")
        self.model.to(self.device)
        self.model.eval()
        logger.info("Transformer model from path %s loaded successfully", model_dir)
        self.initialized = True

    def preprocess(self, data):
        logger.info(f"Data is of type {type(data)}, data[0]: {data[0]}")
        text = data[0].get("data")
        if text is None:
            text = data[0].get("body")
        sentences = text.decode('utf-8')
        logger.info("Received text: '%s'", sentences)

        inputs = self.tokenizer([sentences+self.tokenizer.eos_token], return_tensors="pt")
        logger.info(f"Encoded input: {inputs}")
        return inputs

    def inference(self, input_batch):
        logger.info(f"input_batch type: {type(input_batch)}")
        # generations = self.model.generate(input_batch.to(self.device))
        # generations = self.tokenizer.batch_decode(generations, skip_special_tokens=True)
        input_batch.to(self.device)
        logging.info(f"Input to model {input_batch}")
        # output = self.model.generate(**input_batch)
        output = self.model.generate(input_ids=input_batch['input_ids'], attention_mask=input_batch['attention_mask'])

        logging.info(f"Output {output}")

        return output

    def postprocess(self, inference_output):
        return self.tokenizer.batch_decode(inference_output, skip_special_tokens=True)

    def handle(self, data, context):
        return super().handle(data, context)


if __name__ == '__main__':
    handler = TranslationHandler()
