# SPDX-FileCopyrightText: Copyright 2024 Siemens AG
# SPDX-License-Identifier: MIT

from .implementations import Implementation
from dataclasses import dataclass
from .graders import Grader, GraderHolders
from .models import Model, ModelEvalResult
from typing import Any, Self
from pathlib import Path
import os
from .system_prompts import parse_system_prompt, merge_system_prompts
from .parse_context import ParseContext


@dataclass(frozen=True)
class TaskEvalResult:
    name: str
    models: dict[str, ModelEvalResult]


@dataclass(frozen=True)
class Task:
    name: str
    models: list[str]
    system_prompts: dict[str, str]
    user_prompt: list[tuple[str, str]]
    graders: GraderHolders
    metadata: dict[str, Any]

    @staticmethod
    def parse(
        pc: ParseContext,
        config_parent: Path,
        tasks: list[dict[str, Any]],
        models: dict[str, Model],
        tasksets_models: list[str],
        graders: dict[str, Grader],
    ) -> list["Task"]:
        result: list["Task"] = []
        for task in tasks:
            name = pc.get_value(task, "name")
            with pc.context(f"[{name}]") as pc:
                pc.report("Parsing task")
                try:
                    task_models = task.get("models", None)
                    if task_models is None:
                        task_models = tasksets_models

                    if "default" in task_models:
                        raise ValueError(
                            f"`default` used in task `{name}` is a reserved model name"
                        )
                    undefined_models = [
                        model for model in task_models if model not in models
                    ]
                    if undefined_models:
                        pc.raise_error(f"Undefined models {undefined_models}")

                    system_prompt = task.get("system_prompts", None)
                    with pc.context("system_prompts") as pc:
                        system_prompt = parse_system_prompt(pc, system_prompt, models)

                    user_prompt = pc.get_value(task, "user_prompt")
                    with pc.context("user_prompt") as pc:
                        user_prompt = _parse_user_prompt(pc, config_parent, user_prompt)

                    task_graders = pc.get_value(task, "graders")
                    with pc.context("graders") as pc:
                        pc.report("Configure graders")
                        task_graders = GraderHolders.configure_graders(
                            pc, task_graders, graders
                        )

                    metadata = task.get("metadata", None)
                    result.append(
                        Task(
                            name,
                            task_models,
                            system_prompt,
                            user_prompt,
                            task_graders,
                            metadata or {},
                        )
                    )

                except Exception as e:
                    pc.raise_error(cause=e)

        return result

    def evaluate(
        self: Self,
        ec: ParseContext,
        parent_system_prompts: dict[str, dict[str, str]],
        models: dict[str, Model],
        grader_context: dict[str, Any],
    ) -> TaskEvalResult:
        model_results = {}

        resolved_system_prompt = merge_system_prompts(
            parent_system_prompts,
            self.system_prompts,
        )

        with ec.context("models") as ec:
            for model_name in self.models:
                with ec.context(f"[{model_name}]") as ec:
                    ec.report("Evaluating model")

                    model = models[model_name]
                    if model is None:
                        ec.raise_error("Could not find model")

                    model_results[model.name] = model.evaluate(
                        ec,
                        resolved_system_prompt,
                        self.user_prompt,
                        self.graders,
                        grader_context,
                    )

        return TaskEvalResult(self.name, model_results)


def _extract_user_prompt(prompt: dict[str, str]) -> tuple[str, str]:
    key = next(iter(prompt))
    elem = prompt[key]
    return key, elem


def _parse_user_prompt(
    pc: ParseContext, config_dir: Path, prompt_line: list[dict[str, str]]
) -> list[tuple[str, str]]:
    try:
        temp: list[tuple[str, str]] = []
        for elem in prompt_line:
            key, value = _extract_user_prompt(elem)
            with pc.context(key) as pc:
                value = elem[key]
                if key == "python":
                    impl = Implementation.parse(pc, {"python": value})
                    prompts = impl.invoke()
                    for prompt in prompts:
                        temp.append(prompt)
                elif key == "image":
                    if not os.path.isabs(value):
                        value = (config_dir / value).as_posix()
                    path = Path(value)
                    if not path.exists():
                        pc.raise_error(f"File '{path.resolve()}' does not exist")
                    temp.append(("image", value))
                else:
                    temp.append((key, value))

        return temp

    except Exception as e:
        pc.raise_error(cause=e)
