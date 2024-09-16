# SPDX-FileCopyrightText: Copyright 2024 Siemens AG
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any
from .implementations import Implementation
from .parse_context import ParseContext
import base64
import time
from .graders import GraderHolders, GraderResults


@dataclass
class Answer:
    value: str
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
    duration: float


@dataclass(frozen=True)
class ModelEvalResult:
    name: str
    answer: str
    duration: float
    grader_result: GraderResults


class Model:
    def __init__(self, name: str) -> None:
        self.name = name

    def request_answer(self, system_prompt: str, prompts: list[tuple[str, str]]) -> str:
        raise

    @staticmethod
    def parse(pc: ParseContext, models: dict[str, Any]) -> dict[str, "Model"]:
        result = {}
        for key, value in models.items():
            with pc.context(key) as pc:
                pc.report("Parsing model")
                try:
                    name = key
                    if name == "default":
                        raise ValueError("`default` is a reserved model name")

                    impl = pc.get_value(value, "implementation")
                    with pc.context("implementation") as pc:
                        impl = Implementation.parse(pc, impl)
                        try:
                            model_instance = impl.parsing_invoke(
                                pc, {"name": key, "config": value}
                            )
                            result[name] = model_instance
                        except Exception as e:
                            pc.raise_error(cause=e)

                except Exception as e:
                    pc.raise_error(cause=e)
        return result

    def execute_prompt(
        self,
        ec: ParseContext,
        system_prompt: dict[str, str],
        user_prompts: list[tuple[str, str]],
    ) -> Answer:
        raise NotImplementedError

    def _extract_prompt(self, prompt: dict[str, str]) -> tuple[str, str]:
        key = next(iter(prompt))
        elem = prompt[key]
        return key, elem

    def _extends(
        self, prompts: list[dict[str, str]] | list[tuple[str, str]]
    ) -> list[dict[str, Any]]:
        content: list[dict[str, Any]] = []
        for prompt in prompts:
            if isinstance(prompt, dict):
                key, value = self._extract_prompt(prompt)
            else:
                key, value = prompt[0], prompt[1]

            if key == "text":
                content.append({"type": "text", "text": value})
            elif key == "image":
                with open(value, "rb") as image_file:
                    value = base64.b64encode(image_file.read()).decode("utf-8")
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{value}"},
                    }
                )

        return content

    def evaluate(
        self,
        ec: ParseContext,
        system_prompt: dict[str, str],
        user_prompts: list[tuple[str, str]],
        graders: GraderHolders,
        grader_context: dict[str, Any],
    ) -> ModelEvalResult:
        try:
            start = time.time()
            answer = self.execute_prompt(ec, system_prompt, user_prompts)
            duration = time.time() - start
            ec.report(f"Evaluating model took {duration:.2f} seconds")
        except Exception as e:
            ec.raise_error("Failed to call llm", cause=e)

        context = {
            "system_prompt": system_prompt,
            "user_prompts": user_prompts,
            "current_model": self,
        }

        merged_context = grader_context | context

        with ec.context("graders") as ec:
            graders_result = graders.evaluate(ec, merged_context, answer.value)
            return ModelEvalResult(
                self.name, answer.value, answer.duration, graders_result
            )
