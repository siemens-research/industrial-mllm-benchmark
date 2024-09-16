# SPDX-FileCopyrightText: Copyright 2024 Siemens AG
# SPDX-License-Identifier: MIT

from .implementations import Implementation
from .models import Model
from .parse_context import ParseContext
from typing import Any


def parse_system_prompt(
    pc: ParseContext, system_prompts: dict[str, Any] | None, models: dict[str, Model]
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    if system_prompts is None:
        return result

    model_names = set(models.keys())
    model_names.add("default")

    for key in model_names:
        with pc.context(key) as pc:
            try:
                system_prompt = system_prompts.get(key, None)
                if system_prompt is None:
                    continue
                elif isinstance(system_prompt, str):
                    prompt = {"text": system_prompt.strip()}
                else:
                    impl = pc.get_value(system_prompt, "implementation")
                    with pc.context("implementation") as pc:
                        impl = Implementation.parse(pc, impl)
                        prompt = {"text": impl.invoke().strip()}
                result[key] = prompt
            except Exception as e:
                pc.raise_error(cause=e)

    return result


def merge_system_prompts(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    if left and not right:
        return left
    if right and not left:
        return right
    return {**left, **right}
