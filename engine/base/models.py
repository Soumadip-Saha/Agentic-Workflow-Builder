from typing import Literal, Optional, Union
from pydantic import BaseModel, Field, HttpUrl


class OpenAIConfig(BaseModel):
    model_provider: Literal["openai"]
    model: Literal["gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o-mini", "o4-mini", "o3-mini", "gpt-4.1", "gpt-4o"]
    # Two options for api_key_name, OPENAI_API_KEY or GOOGLE_API_KEY
    api_key_name: Literal["OPENAI_API_KEY"]

class GoogleConfig(BaseModel):
    model_provider: Literal["google_genai"]
    model: Literal["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
    api_key_name: Literal["GOOGLE_API_KEY"]

class SelfHostedConfig(BaseModel):
    model_provider: Literal["self-hosted"]
    model: str
    api_key_name: Optional[str] = "xxxxxxxxxxxxxx"
    base_url: HttpUrl

AnyModelConfig = Union[OpenAIConfig, GoogleConfig, SelfHostedConfig]

class LLMParameters(BaseModel):
    temperature: float = Field(default=0.7, ge=0, le=2.0)
    max_tokens: int | None = None
    system_prompt: str | None = None


class ModelWrapper(BaseModel):
    config: AnyModelConfig = Field(discriminator="model_provider")