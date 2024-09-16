<!--
    SPDX-FileCopyrightText: Copyright 2024 Siemens AG
    SPDX-License-Identifier: MIT
-->
# Industrial Multimodal LLM Benchmark

## License

This project is using the [MIT license](./LICENSE).

## Installation

Currently you need to us poetry to install the Industrial MLLM Benchmark on your system.
In the future you will be able to use `pip` for that.

The Industrial MLLM Benchmark was developed and tested under Python 3.11. It might work
with different Python Version but it was not tested yet.

**Prerequisits:**

* Python 3.11
* [Poetry](https://python-poetry.org/)
* Git

When you have installed the prerequisits you can install the Industrial MLLM Benchmark like this:

```cmd
git clone https://github.com/siemens-research/industrial_mllm_benchmark.git

cd industrial_mllm_benchmark

poetry install
```

## Usage

Our example benchmark assumes, that you have access to OpenAI (for details please have a look at)
[examples/models.yml](examples/models.yml).
As best practice we don't have put the concrete endpoint or api key into the benchmark
configuration file. Instead we expect them in environment variables.
The example benchmark expects the following environment variables:

| Environment Varialbe | Description                         |
|----------------------|-------------------------------------|
| MODEL1_ENDPOINT      | The endpoint url of the first model, without any refernce to the actuel OpenAI model or version |
| MODEL1_ACCESS_TOKEN  | The API Key for accessing the end point of the first model. |
| MODEL2_ENDPOINT      | The endpoint url of the second model. |
| MODEL2_ACCESS_TOKEN  | The API Key for accessing the end point of the second model. |

You can either import these varibles into your environment, or you can store them inside a file with the extension `.env`.

benchmark.env

```.env
# Please replace the <PLACEHOLDER>s with your actual values
MODEL1_ENDPOINT=<YOUR ENDPOINT FOR MODEL1>
MODEL1_ACCESS_TOKEN=<YOUR API KEY FOR MODEL1>

MODEL2_ENDPOINT=<YOUR ENDPOINT FOR MODEL2>
MODEL2_ACCESS_TOKEN=<YOUR API KEY FOR MODEL2>
```

With the command

```cmd
poetry run industrial_mllm_benchmark
    --env-file benchmark.env
    execute -c examples/benchmark.yml
```

you will execute the benchmark and store the results in the file `benchmark.json`

There is also a [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/) template available to create
a html report page based on the result file. You can create this report page with

```cmd
poetry run industrial_mllm_benchmark
    --env-file benchmark.env
    report --json benchmark.yml --jinja2 templates/report.html.j2
```
