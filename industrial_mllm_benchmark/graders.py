# SPDX-FileCopyrightText: Copyright 2024 Siemens AG
# SPDX-License-Identifier: MIT

from .implementations import Implementation
from dataclasses import dataclass
from typing import Any
import time
from .parse_context import ParseContext


@dataclass(frozen=True)
class Grader:
    name: str
    description: str
    implementation: Implementation

    @staticmethod
    def parse(pc: ParseContext, graders: dict[str, Any]) -> dict[str, "Grader"]:
        result = {}
        for name, grader in graders.items():
            with pc.context(f"[{name}]") as pc:
                pc.report("Parsing grader")
                try:
                    description = pc.get_value(grader, "description")
                    implementation = pc.get_value(grader, "implementation")
                    impl = Implementation.parse(pc, implementation)

                    result[name] = Grader(name, description, impl)
                except Exception as e:
                    pc.raise_error(cause=e)

        return result


@dataclass(frozen=True)
class GraderHolder:
    """Contains a single configured task grader and its weight"""

    grader: Grader
    weight: float
    expected_answer: str

    @property
    def name(self) -> str:
        return self.grader.name


@dataclass(frozen=True)
class GraderResult:
    name: str
    result: float


@dataclass(frozen=True)
class GraderResults:
    threshold: float
    combined_result: float
    status: str
    results: list[GraderResult]


@dataclass(frozen=True)
class GraderHolders:
    """Contains a list of configured task graders."""

    threshold: float
    graders: list[GraderHolder]

    @staticmethod
    def configure_graders(
        pc: ParseContext, config: dict[str, Any], grader_maps: dict[str, Grader]
    ) -> "GraderHolders":
        try:
            threshold = pc.get_value(config, "threshold")
            graders = []
            for item in pc.get_value(config, "use"):
                with pc.context("use") as pc:
                    name = pc.get_value(item, "name")
                    if name in grader_maps:
                        with pc.context(f"[{name}]") as pc:
                            pc.report("Configure grader")
                            grader = grader_maps[name]
                            weight = float(pc.get_value(item, "weight"))
                            expected_answer = pc.get_value(item, "answer")
                            graders.append(
                                GraderHolder(grader, weight, expected_answer)
                            )

            return GraderHolders(threshold, graders)
        except Exception as e:
            pc.raise_error(cause=e)

    def evaluate(
        self, ec: ParseContext, context: dict[str, Any], actual_answer: str
    ) -> GraderResults:
        total = 0.0
        sum_weight = 0.0
        grader_results = []
        exception_happened = False
        total_start = time.time()
        for holder in self.graders:
            name = holder.name
            with ec.context(f"{name}") as ec:
                weight = holder.weight
                sum_weight += weight
                expected_answer = holder.expected_answer

                args = {
                    "ec": ec,
                    "context": context,
                    "actual_answer": actual_answer,
                    "expected_answer": expected_answer,
                }
                grader = holder.grader

                start = time.time()
                ## TODO: capture exception and report them during eval
                ## QUESTIONS: How to handle if a grader fails? Fail the test?
                try:
                    result = grader.implementation.invoke(args)
                    if isinstance(result, bool):
                        result = 1.0 if result else 0.0

                except Exception as error:
                    ec.report(str(error))
                    exception_happened = True
                    result = 0.0  # fail

                duration = time.time() - start
                ec.report(f"grading took {duration:.2f} seconds, result: {result}")

                grader_results.append(GraderResult(name, result))
                total += weight * float(result)

        total /= sum_weight
        if exception_happened:
            status = "error"
            total = -1.0
        elif total < self.threshold:
            status = "fail"
        else:
            status = "pass"

        total_duration = time.time() - total_start
        ec.report(
            f"grading took {total_duration:.2f} seconds, status: {status}, result: {total:.2f}, threshold: {self.threshold}"
        )

        return GraderResults(self.threshold, total, status, grader_results)
