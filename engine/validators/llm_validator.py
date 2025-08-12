import logging
from langchain.chat_models import init_chat_model

from ..base.models import GoogleConfig, OpenAIConfig, SelfHostedConfig
from ..base.nodes import LLMNode
import os
# from settings.app_settings import settings

async def check_llm_node_connectivity(node: LLMNode):
    """

    Performs a simple invocation to confirm the client is working.
    This is used for validation during workflow builder.
    """
    try:
        if isinstance(node.model.config, OpenAIConfig):
            model_provider = node.model.config.model_provider
            api_key = os.getenv(node.model.config.api_key_name)
            if api_key is None:
                raise ValueError(f"API key for {model_provider} not found in environment variables.")
            model = init_chat_model(
                model_provider=model_provider,
                model=node.model.config.model,
                api_key=api_key
            )
        elif isinstance(node.model.config, GoogleConfig):
            model_provider = node.model.config.model_provider
            api_key = os.getenv(node.model.config.api_key_name)
            if api_key is None:
                raise ValueError(f"API key for {model_provider} not found in environment variables.")
            model = init_chat_model(
                model_provider=model_provider,
                model=node.model.config.model,
                api_key=api_key
            )
        elif isinstance(node.model.config, SelfHostedConfig):
            model_provider = "openai"
            api_key = node.model.config.api_key_name
            base_url = node.model.config.base_url
            model = init_chat_model(
                model_provider=model_provider,
                model=node.model.config.model,
                api_key=api_key, base_url = base_url
            )

        logging.info(f"Checking LLM connectivity for {node.model.config.model_provider}:{node.model.config.model}")
        _ = await model.ainvoke("Checking connectivity")
        logging.info("LLM client connectivity check successful.")
    except Exception as e:
        raise ConnectionError(f"LLM client connectivity check failed for {node.model.config.model_provider}:{node.model.config.model}.\nError: {e}")