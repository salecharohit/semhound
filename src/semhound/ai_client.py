import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

import yaml


_SYSTEM_PROMPT_DEFAULT = (
    "You are a senior application security engineer performing code review. "
    "Evaluate whether the provided code snippet is a true positive security finding. "
    "Be concise and precise."
)

_USER_PROMPT_TEMPLATE = """\
Rule: {rule_message}

Code snippet:
{code_snippet}

Respond in JSON only — no markdown, no explanation outside the JSON object:
{{"confidence": <integer 0-100>, "true_positive": <true or false>, "reasoning": "<one sentence>"}}"""


def _parse_ai_response(text: str) -> Tuple[str, str]:
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if not match:
        return "ERROR", "ERROR"
    try:
        data = json.loads(match.group())
        confidence = str(data.get("confidence", "ERROR"))
        true_positive = str(data.get("true_positive", "ERROR"))
        return confidence, true_positive
    except (json.JSONDecodeError, KeyError):
        return "ERROR", "ERROR"


class BaseAIClient(ABC):
    def __init__(self, config: dict):
        self.model = config.get("model", "")
        self.system_prompt = config.get("system_prompt", _SYSTEM_PROMPT_DEFAULT)

    @abstractmethod
    def analyze(self, code_snippet: str, rule_message: str) -> Tuple[str, str]:
        """Return (confidence_score, true_positive) as strings."""

    def _build_user_prompt(self, code_snippet: str, rule_message: str) -> str:
        return _USER_PROMPT_TEMPLATE.format(
            rule_message=rule_message,
            code_snippet=code_snippet,
        )


class ClaudeClient(BaseAIClient):
    def __init__(self, config: dict):
        super().__init__(config)
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "Anthropic SDK not installed. Run: pip install semhound"
            ) from None
        self._client = anthropic.Anthropic(api_key=config["api_key"])

    def analyze(self, code_snippet: str, rule_message: str) -> tuple[str, str]:
        response = self._client.messages.create(
            model=self.model or "claude-sonnet-4-6",
            max_tokens=256,
            system=self.system_prompt,
            messages=[{"role": "user", "content": self._build_user_prompt(code_snippet, rule_message)}],
        )
        return _parse_ai_response(response.content[0].text)


class GeminiClient(BaseAIClient):
    def __init__(self, config: dict):
        super().__init__(config)
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "Google Generative AI SDK not installed. Run: pip install semhound"
            ) from None
        genai.configure(api_key=config["api_key"])
        self._model = genai.GenerativeModel(
            model_name=self.model or "gemini-1.5-pro",
            system_instruction=self.system_prompt,
        )

    def analyze(self, code_snippet: str, rule_message: str) -> tuple[str, str]:
        response = self._model.generate_content(self._build_user_prompt(code_snippet, rule_message))
        return _parse_ai_response(response.text)


class OpenAIClient(BaseAIClient):
    def __init__(self, config: dict):
        super().__init__(config)
        try:
            import openai
        except ImportError:
            raise ImportError(
                "OpenAI SDK not installed. Run: pip install semhound"
            ) from None
        self._client = openai.OpenAI(api_key=config["api_key"])

    def analyze(self, code_snippet: str, rule_message: str) -> tuple[str, str]:
        response = self._client.chat.completions.create(
            model=self.model or "gpt-4o",
            max_tokens=256,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self._build_user_prompt(code_snippet, rule_message)},
            ],
        )
        return _parse_ai_response(response.choices[0].message.content)


class BedrockClient(BaseAIClient):
    """Uses the Bedrock Converse API — model-agnostic, works with any Bedrock-hosted model."""

    def __init__(self, config: dict):
        super().__init__(config)
        try:
            import boto3
        except ImportError:
            raise ImportError(
                "boto3 not installed. Run: pip install semhound"
            ) from None
        profile = config.get("aws_profile")
        region = config.get("aws_region", "us-east-1")
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        self._client = session.client("bedrock-runtime", region_name=region)
        self._model_id = self.model or "anthropic.claude-3-5-sonnet-20241022-v2:0"

    def analyze(self, code_snippet: str, rule_message: str) -> tuple[str, str]:
        response = self._client.converse(
            modelId=self._model_id,
            system=[{"text": self.system_prompt}],
            messages=[{"role": "user", "content": [{"text": self._build_user_prompt(code_snippet, rule_message)}]}],
            inferenceConfig={"maxTokens": 256},
        )
        text = response["output"]["message"]["content"][0]["text"]
        return _parse_ai_response(text)


_PROVIDER_MAP = {
    "claude": ClaudeClient,
    "gemini": GeminiClient,
    "openai": OpenAIClient,
    "bedrock": BedrockClient,
}


def get_ai_client(config_path: Optional[str]) -> Optional[BaseAIClient]:
    if config_path is None:
        return None
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"AI config not found: {config_path}")
    with open(path) as f:
        config = yaml.safe_load(f)
    provider = config.get("provider", "").lower()
    cls = _PROVIDER_MAP.get(provider)
    if cls is None:
        raise ValueError(f"Unknown AI provider '{provider}'. Choose from: {', '.join(_PROVIDER_MAP)}")
    return cls(config)
