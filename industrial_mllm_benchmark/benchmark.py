# SPDX-FileCopyrightText: Copyright 2024 Siemens AG
# SPDX-License-Identifier: MIT

from pathlib import Path
from dataclasses import dataclass
from .models import Model
from .graders import Grader
from .env_yaml import load_yaml
from .tasksets import Tasksets
from .tasks import TaskEvalResult
import os
from .system_prompts import parse_system_prompt
from .parse_context import ParseContext
from typing import Any
import logging

logger = logging.getLogger(__name__)


def _import_config(pc: ParseContext, config: Path) -> dict[str, Any]:
    try:
        value = load_yaml(config)
        with pc.context("includes") as pc:
            pc.report("Parsing includes")
            includes = value.get("includes", None)
            if includes:
                for include in includes:
                    with pc.context(f"[{include}]") as pc:
                        pc.report("Parsing include")
                        if os.path.isabs(include):
                            include_path = include
                        else:
                            include_path = config.parent / include

                        if not include_path.exists() or not include_path.is_file():
                            pc.raise_error(
                                f"'{include_path}' does not exist or is no file"
                            )

                        try:
                            include_value = load_yaml(include_path)
                            value.update(include_value)
                        except Exception as e:
                            pc.raise_error(
                                f"Error while processing '{include_path}'", e
                            )

                del value["includes"]

            return value
    except Exception as e:
        pc.raise_error("Error while processing includes", e)


@dataclass(frozen=True)
class Benchmark:
    models: dict[str, Model]
    graders: dict[str, Grader]
    system_prompts: dict[str, dict[str, str]]
    tasksets: dict[str, Tasksets]

    @staticmethod
    def parse(pc: ParseContext, config_path: Path) -> "Benchmark":
        with pc.context(f"[{config_path}]") as pc:
            pc.report("Parsing benchmark configuration")
            config = _import_config(pc, config_path)

            models = pc.get_value(config, "models")
            with pc.context("models") as pc:
                pc.report("Parsing model definitions")
                models = Model.parse(pc, models)

            graders = pc.get_value(config, "graders")
            with pc.context("graders") as pc:
                pc.report("Parsing grader definitions")
                graders = Grader.parse(pc, graders)

            with pc.context("system_prompts") as pc:
                pc.report("Parsing global system prompts")
                system_prompts = parse_system_prompt(
                    pc, config.get("system_prompts", None), models
                )

            with pc.context("tasksets") as pc:
                pc.report("Parsing tasksets")
                tasksets = pc.get_value(config, "tasksets")
                tasksets = Tasksets.parse(
                    pc, config_path.parent, tasksets, models, graders
                )

            return Benchmark(models, graders, system_prompts, tasksets)

    def evaluate(self, ec: ParseContext) -> dict[str, dict[str, TaskEvalResult]]:
        # task.name -> model.name -> grading-result
        task_set_result: dict[str, dict[str, TaskEvalResult]] = {}

        with ec.context("tasksets") as ec:
            for taskset_name, taskset in self.tasksets.items():
                with ec.context(f"[{taskset_name}]") as ec:
                    task_set_result[taskset_name] = taskset.evaluate(
                        ec, self.system_prompts, self.models
                    )

        return task_set_result
