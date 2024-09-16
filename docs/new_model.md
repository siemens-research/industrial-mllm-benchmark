<!--
    SPDX-FileCopyrightText: Copyright 2024 Siemens AG
    SPDX-License-Identifier: MIT
-->
# Industrial LLM Benchmark

## Adding a new model definition

To add a model, just go into the benchmark configuration file and into the section `models`
or if you have externalized the model definitions go to that file and there into the
`models` section the following:

```yaml
  new_model:
    implementation:
      language: python
      module: industrial_mllm_benchmark
      class: OpenAIModel
      function: parse_instance
    endpoint: <PLACEHOLDER>
    access_token: <PLACEHOLDER>
    model: gpt-4o
    version: 2023-07-01-preview
    parameters:
      temperature: 0.0
      top_p: 0.95
      max_tokens: 2000
```

Replace `new_model` with your model name, but ensure that is unique for the benchmarks you are using.
Please keep the block `implementation` as it is, as it points to the benchmark implementation
of the OpenAI models. In the future we will also explain, how you can add your own models, or local models to the benchmark (looking forward to any contribution to this project).

The keys `endpoint`, `access_token`, `model`, `version` and `paramters` are configuration details
for the OpenAI model.

`endpoint` should contain the http(s) url to the endpoint you are using, but only mention here
the raw endpoint without any paths or url parameters.
`acess_token` is required so the endpoint will accept our requests on your behalf.
`model` is now the actual model you want to use on your endpoint
`version` is the version of your model you want to use.
In the `paramters` section you can specify the OpenAI parameters you want to send when you
request a response.

**_IMPORTANT:_** We recommend highly **not** to add your endpoint or access_token directly in your
benchmark configuration, but store them in environment variables and mention those in your yaml file. You can use the following syntax that do that:

```yaml
    endpoint: !ENV ${ENDPOINT}
    access_token: !ENV ${ACCESS_KEY}
```
