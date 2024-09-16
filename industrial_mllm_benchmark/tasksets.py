# SPDX-FileCopyrightText: Copyright 2024 Siemens AG
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from .models import Model
from .graders import Grader
from .tasks import Task, TaskEvalResult
from pathlib import Path
from .system_prompts import parse_system_prompt, merge_system_prompts
from .parse_context import ParseContext
from typing import Any


@dataclass(frozen=True)
class Tasksets:
    name: str
    system_prompts: dict[str, str]
    tasks: list[Task]

    @staticmethod
    def parse(
        pc: ParseContext,
        config_parent: Path,
        tasksets: list[dict[str, Any]],
        models: dict[str, Model],
        graders: dict[str, Grader],
    ) -> dict[str, "Tasksets"]:
        result: dict[str, "Tasksets"] = {}

        for taskset in tasksets:
            name = pc.get_value(taskset, "name")
            with pc.context(f"[{name}]") as pc:
                pc.report("Parsing taskset")
                system_prompt = taskset.get("system_prompts", None)
                with pc.context("system_prompts") as pc:
                    system_prompt = parse_system_prompt(pc, system_prompt, models)

                taskset_models = taskset.get("models", None)
                if taskset_models is None:
                    taskset_models = list(models.keys())

                tasks = pc.get_value(taskset, "tasks")
                with pc.context("tasks") as pc:
                    pc.report("Parsing tasks")
                    tasks = Task.parse(
                        pc, config_parent, tasks, models, taskset_models, graders
                    )

                result[name] = Tasksets(name, system_prompt, tasks)

        return result

    def evaluate(
        self,
        ec: ParseContext,
        parent_system_prompts: dict[str, dict[str, str]],
        models: dict[str, Model],
    ) -> dict[str, TaskEvalResult]:
        ec.report("Evaluating tasksets")
        task_result = {}

        grader_context = {"models": models}

        with ec.context("task") as ec:
            for task in self.tasks:
                with ec.context(f"[{task.name}]") as ec:
                    ec.report("Evaluating task")
                    resolved_system_prompts = merge_system_prompts(
                        parent_system_prompts, self.system_prompts
                    )
                    task_result[task.name] = task.evaluate(
                        ec, resolved_system_prompts, models, grader_context
                    )

        return task_result
