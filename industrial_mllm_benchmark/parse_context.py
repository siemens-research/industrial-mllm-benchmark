# SPDX-FileCopyrightText: Copyright 2024 Siemens AG
# SPDX-License-Identifier: MIT

from typing import Self, Generator, Callable, NoReturn, Any
from contextlib import contextmanager

import logging

logger = logging.getLogger(__name__)


class ParseContext:
    def __init__(
        self,
        path: str | None = None,
        reporter: Callable[["ParseContext", str], None] | None = None,
    ):
        self._path = []
        self.reporter = reporter
        if path is not None:
            self._path.append(path)

    @contextmanager
    @staticmethod
    def root(
        path: str | None, reporter: Callable[["ParseContext", str], None] | None = None
    ) -> Generator["ParseContext", None, None]:
        pc = ParseContext(path, reporter)
        yield pc

    @contextmanager
    def context(self, context: str) -> Generator[Self, None, None]:
        try:
            self._path.append(context)
            logger.debug(f"Enter context: {context}")
            yield self
        finally:
            self._path.pop()
            logger.debug(f"Leaving context: {context}")

    def __str__(self) -> str:
        return "/".join(self._path)

    def raise_error(
        self,
        message: str | None = None,
        cause: Exception | None = None,
        force_wrap: bool = False,
    ) -> NoReturn:
        if cause is None:
            raise ParseException(message, self)
        elif isinstance(cause, ParseException) and not force_wrap:
            raise cause
        else:
            raise ParseException(message, self, cause)

    def get_value(self, dict: dict[str, Any], key: str) -> Any:
        if key in dict:
            return dict[key]
        return self.raise_error(f"missing key: {key}")

    def report(self, message: str):
        if self.reporter:
            self.reporter(self, message)


class ParseException(Exception):
    def __init__(
        self,
        message: str | None,
        parse_context: ParseContext,
        cause: Exception | None = None,
    ):
        if message:
            message = f"({parse_context}): {message}"
        else:
            message = str(parse_context)

        if cause:
            message += f" <- ({cause.__repr__()})"

        super().__init__(message)
        self.parse_context = parse_context
        self.cause = cause
