# SPDX-FileCopyrightText: Copyright 2024 Siemens AG
# SPDX-License-Identifier: MIT

import click
from .benchmark import Benchmark
from pathlib import Path
from .implementations import PythonImplementation
from dotenv import load_dotenv
import time
import json
from typing import Any, Callable
import logging
from .parse_context import ParseContext


def sanitize_json_output(o) -> Any:
    """Removes function type from json output"""
    temp = vars(o)
    if type(o) == PythonImplementation:
        temp = vars(o)
        if "func" in temp:
            del temp["func"]
    elif "access_token" in temp:
        temp["access_token"] = "### REDACTED ###"

    return temp


def extract_jinja2_extension(path: Path) -> str:
    """Extracts the extension of the Jinja2 template"""
    parts = str(path.name).split(".")
    if parts[-1] != "j2" or len(parts) < 3:
        raise BaseException(
            "The configuration file is not a Jinja2 template (does not end in '.<doc_ext>.j2' )"
        )
    return parts[-2]


def stdout_reporter(pc: ParseContext, message: str) -> None:
    print(f"{pc}: {message}")


def logger_reporter(pc: ParseContext, message: str) -> None:
    logging.getLogger("reporter").info(f"{pc}: {message}")


def none_reporter(pc: ParseContext, message: str) -> None:
    pass


@click.group()
@click.option(
    "-x",
    "--show-stacktrace",
    type=bool,
    is_flag=True,
    default=False,
    help="Show stacktrace on error",
)
@click.option(
    "--env-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to the environment variables file",
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["NONE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    default="NONE",
    help="Set the log level",
)
@click.option(
    "--ignore-logger",
    type=str,
    required=False,
    help="List of loggers to ignore (comma separated)",
)
@click.option(
    "--reporter",
    type=click.Choice(["none", "stdout", "logger"], case_sensitive=False),
    default="stdout",
    help="Set the reporter",
)
@click.pass_context
def cli(
    ctx: click.Context,
    show_stacktrace: bool,
    env_file: Path | None,
    log_level: str,
    ignore_logger: str,
    reporter: str,
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["show_stacktrace"] = show_stacktrace

    reporter_func: Callable[[ParseContext, str], None] = none_reporter
    if reporter == "stdout":
        reporter_func = stdout_reporter
    elif reporter == "logger":
        reporter_func = logger_reporter

    ctx.obj["reporter"] = reporter_func

    if log_level != "NONE":
        logging.basicConfig(level=log_level)

    if ignore_logger:
        disabled_logger = ignore_logger.split(",")
        for name in disabled_logger:
            logging.getLogger(name).setLevel(logging.WARNING)

    if env_file:
        load_dotenv(env_file)


@cli.command()
@click.option(
    "-d",
    "--dest-dir",
    type=click.Path(dir_okay=True, path_type=Path),
    default=".",
    show_default=True,
    help="Path where the generated report should be stored",
)
@click.option(
    "--json",
    "json_input",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to the JSON benchmark result file",
)
@click.option(
    "--jinja2",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Path to the Jinja2 template and the output file",
)
@click.pass_context
def report(
    ctx,
    dest_dir: Path,
    json_input: Path,
    jinja2: Path,
) -> None:
    """Generates an report based on the benchmark result and report template."""

    try:
        with ParseContext.root("[report]", ctx.obj["reporter"]) as rc:
            json_base_name = json_input.stem

            rc.report(f"Reading json `{json_input}`")
            with json_input.open("r") as f:
                content = json.load(f)

            with rc.context("jinja2") as rc:
                from jinja2 import Environment, FileSystemLoader

                jinja2_ext = extract_jinja2_extension(jinja2)
                jinja2_path = Path(jinja2.as_posix()).resolve()
                relative = jinja2_path.relative_to(jinja2_path.parent)

                env = Environment(
                    loader=FileSystemLoader(searchpath=jinja2_path.parent)
                )

                rc.report(f"Rendering Jinja2 template `{jinja2}`")
                template = env.get_template(str(relative))

            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / f"{json_base_name}.{jinja2_ext}"
            rc.report(f"Storing rendered file as `{dest_file}`")
            with dest_file.open("w", encoding="utf8") as f:
                f.write(template.render(result=content))

    except Exception as e:
        if ctx.obj["show_stacktrace"]:
            raise e
        else:
            print(f"Error: {e}")


@cli.command()
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default="benchmark.yml",
    show_default=True,
    help="Path to the benchmark configuration file",
)
@click.option(
    "-d",
    "--dest-dir",
    type=click.Path(dir_okay=True, path_type=Path),
    default=".",
    show_default=True,
    help="Path where the output files should be placed",
)
@click.pass_context
def execute(ctx, config: Path, dest_dir: Path):
    """Executes the specified multimodal LLM benchmark."""

    try:
        with ParseContext.root("[execute]", ctx.obj["reporter"]) as pc:
            with pc.context("parse") as pc:
                benchmark = Benchmark.parse(pc, config)

            with pc.context("evaluate") as pc:
                start = time.time()
                result = benchmark.evaluate(pc)
                duration = time.time() - start

                pc.report(f"Evaluation took {duration:.2f} seconds")

            output = {"config": benchmark, "evaluation": result}

            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / f"{config.stem}.json"
            pc.report(f"Storing config and evaluation as JSON in `{dest_file}`")
            with dest_file.open("w", encoding="utf-8") as f:
                json.dump(output, f, default=sanitize_json_output, indent=2)

    except Exception as e:
        if ctx.obj["show_stacktrace"]:
            raise e
        else:
            print(f"Error: {e}")


if __name__ == "__main__":
    cli()
