# SPDX-FileCopyrightText: Copyright 2024 Siemens AG
# SPDX-License-Identifier: MIT

from typing import Self, Any
import importlib
from .parse_context import ParseContext


class Implementation:
    def __init__(self) -> None:
        pass

    def invoke(self: Self, args: dict[str, Any] = {}) -> Any:
        raise NotImplementedError

    def parsing_invoke(
        self: Self, pc: ParseContext, args: dict[str, Any] | None = None
    ) -> Any:
        raise NotImplementedError

    @staticmethod
    def parse(pc: ParseContext, config: dict[str, Any]) -> "Implementation":
        try:
            language = pc.get_value(config, "language")
            if language == "python":
                with pc.context("python") as pc:
                    pc.report("Parsing python implementation")
                    return PythonImplementation.parse(pc, config)
            else:
                pc.raise_error(f"Unsupported language: {language}")

        except Exception as e:
            pc.raise_error(cause=e)


class PythonImplementation(Implementation):
    def __init__(
        self,
        module_name: str,
        class_name: str,
        function_name: str,
        args: dict[str, Any],
    ) -> None:
        self.module = module_name
        self.function = function_name
        self.args = args
        attr_handle = importlib.import_module(module_name)
        if class_name:
            attr_handle = getattr(attr_handle, class_name)

        self.func = getattr(attr_handle, function_name)

    def invoke(self, args: dict[str, Any] = {}) -> Any:
        args = args or {}
        mergedArgs = {**self.args, **args}

        return self.func(**mergedArgs)

    def parsing_invoke(
        self: Self, pc: ParseContext, args: dict[str, Any] | None = None
    ) -> Any:
        args = args or {}
        mergedArgs = {**self.args, **args}
        mergedArgs["pc"] = pc

        return self.func(**mergedArgs)

    @staticmethod
    def parse(pc: ParseContext, config: dict[str, Any]) -> "Implementation":
        try:
            module_name = pc.get_value(config, "module")
            function_name = pc.get_value(config, "function")
            class_name = config.get("class", None)
            args = config.get("args", {})

            return PythonImplementation(module_name, class_name, function_name, args)
        except Exception as e:
            pc.raise_error(cause=e)
