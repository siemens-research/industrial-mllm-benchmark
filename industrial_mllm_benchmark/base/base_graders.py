# SPDX-FileCopyrightText: Copyright 2024 Siemens AG
# SPDX-License-Identifier: MIT

from typing import Any
import logging
from inspect import cleandoc as dedent
from ..parse_context import ParseContext as EvalContext

logger = logging.getLogger(__name__)


def contains(
    ec: EvalContext, context: dict[str, Any], expected_answer: str, actual_answer: str
) -> float:
    return 1.0 if expected_answer in actual_answer else 0.0


def expected_answer(
    ec: EvalContext,
    context: dict[str, Any],
    expected_answer: str,
    actual_answer: str,
    grader_model: str,
    system_prompt: str,
    user_prompt: str,
) -> float:
    models = context.get("models", None)
    if models is None:
        raise ValueError("No models found in grader context")

    actual_model = models.get(grader_model, None)
    if actual_model is None:
        raise ValueError(f"Model '{grader_model}' not found in grader context")

    if user_prompt.index("{actual_answer}") < 0:
        raise ValueError("User prompt does not contain '{actual_answer}'")

    if user_prompt.index("{expected_answer}") < 0:
        raise ValueError("User prompt does not contain '{expected_answer}'")

    user_prompt = user_prompt.replace("{actual_answer}", actual_answer).replace(
        "{expected_answer}", expected_answer
    )

    answer = actual_model.execute_prompt(
        ec, {"text": system_prompt}, [{"text": user_prompt}]
    )

    logger.debug(
        dedent(f"""expected_answer grader:
                    actual answer: '{actual_answer}',
                    expected answer: '{expected_answer}',
                    grader answer: '{answer}'
                    """)
    )

    return float(answer.value)
