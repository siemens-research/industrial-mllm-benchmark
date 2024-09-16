# SPDX-FileCopyrightText: Copyright 2024 Siemens AG
# SPDX-License-Identifier: MIT

from ..models import Model, Answer
import requests
import re
import time
from ..parse_context import ParseContext
from typing import Any, Self


class OpenAICompatibleModel(Model):
    def __init__(
        self: Self,
        name: str,
        endpoint: str,
        headers: dict[str, Any],
        parameters: dict[str, Any],
    ) -> None:
        super().__init__(name)
        self.headers = headers
        self.endpoint = endpoint
        self.parameters = parameters

    def _retrying_call_open_ai(
        self, pc: ParseContext, headers: dict[str, Any], payload: dict[str, Any]
    ) -> Answer:
        response = requests.post(self.endpoint, headers=headers, json=payload)
        response_json = response.json()
        if "error" in response_json:
            if response_json["error"]["code"] == "429":
                error_message = response_json["error"]["message"]
                retry_time = re.search(
                    r"Please retry after (\d+) seconds", error_message
                )
                if retry_time:
                    retry_seconds = int(retry_time.group(1))
                    pc.report(f"Rate limited. Retrying in {retry_seconds} seconds...")
                    time.sleep(retry_seconds + 1)
                    return self._retrying_call_open_ai(pc, headers, payload)

            raise Exception(response_json["error"])

        answer = response_json["choices"][0]["message"]["content"]
        tokens = response_json["usage"]

        return Answer(
            answer,
            tokens["completion_tokens"],
            tokens["prompt_tokens"],
            tokens["total_tokens"],
            0.0,
        )

    def _create_payload(
        self, system_prompt: dict[str, str], user_prompts: list[tuple[str, str]]
    ) -> dict[str, Any]:
        raise NotImplementedError

    def execute_prompt(
        self,
        ec: ParseContext,
        system_prompt: dict[str, str],
        user_prompts: list[tuple[str, str]],
    ) -> Answer:
        payload = self._create_payload(system_prompt, user_prompts)

        start = time.time()
        answer = self._retrying_call_open_ai(ec, self.headers, payload)
        duration = time.time() - start
        return Answer(
            answer.value,
            answer.completion_tokens,
            answer.prompt_tokens,
            answer.total_tokens,
            duration,
        )


class OpenAIModel(OpenAICompatibleModel):
    def __init__(
        self,
        name: str,
        access_token: str,
        endpoint: str,
        model: str,
        version: str | None,
        parameters: dict[str, Any],
    ) -> None:
        endpoint = f"{endpoint}/openai/deployments/{model}/chat/completions?api-version={version}"
        headers = {"Content-Type": "application/json", "api-key": access_token}
        super().__init__(name, endpoint, headers, parameters)

    @staticmethod
    def parse_instance(
        pc: ParseContext, name: str, config: dict[str, Any]
    ) -> "OpenAIModel":
        try:
            access_token = pc.get_value(config, "access_token")
            endpoint = pc.get_value(config, "endpoint")
            model = pc.get_value(config, "model")
            version = config.get("version", None)
            parameters = config.get("parameters", {})
            return OpenAIModel(name, access_token, endpoint, model, version, parameters)
        except Exception as e:
            pc.raise_error(cause=e)

    def _create_payload(
        self, system_prompt: dict[str, str], user_prompts: list[tuple[str, str]]
    ) -> dict[str, Any]:
        return {
            "messages": [
                {"role": "system", "content": self._extends([system_prompt])},
                {"role": "user", "content": self._extends(user_prompts)},
            ]
        } | self.parameters


class OllamaModel(OpenAICompatibleModel):
    def __init__(
        self,
        name: str,
        endpoint: str,
        model: str,
        parameters: dict[str, Any],
    ) -> None:
        super().__init__(
            name, endpoint, {"Content-Type": "application/json"}, parameters
        )
        self.model = model

    @staticmethod
    def parse_instance(
        pc: ParseContext, name: str, config: dict[str, Any]
    ) -> "OllamaModel":
        try:
            endpoint = pc.get_value(config, "endpoint")
            model = pc.get_value(config, "model")
            parameters = config.get("parameters", {})
            return OllamaModel(name, endpoint, model, parameters)
        except Exception as e:
            pc.raise_error(cause=e)

    def _create_payload(
        self, system_prompt: dict[str, str], user_prompts: list[tuple[str, str]]
    ) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._extends([system_prompt])},
                {"role": "user", "content": self._extends(user_prompts)},
            ],
        } | self.parameters
