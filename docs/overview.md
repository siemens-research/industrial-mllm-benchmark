<!--
    SPDX-FileCopyrightText: Copyright 2024 Siemens AG
    SPDX-License-Identifier: MIT
-->
# Industrial LLM Benchmark

## Structure of the Benchmark File

The benchmark file is written using [YAML](https://yaml.org/) syntax.

You can find [here](examples/benchmark.yml) our example benchmark file.

Here is a roundup of the benchmark file, it is only meant for documentation purpose
and would fail when you try to run our benchmark on it.

```yaml
models:
    # This section contains a list of model definition, which can be used later
    # in the benchmark configuration file.
    # A model definition tells the benchmark how to interact with a MLLM

graders:
    # This section contains a list of grader definition, which can be used later
    # in the benchmark configuration file.
    # A grader is used to grade the output of MLLM answer to our tasks.

system_prompts:
    # Here you could add a system prompt specific to the models out of the models
    # section. If you use the magic model name `default` it would be used for
    # every model.
    # Probably you don't want to specify the system prompt here, but in the
    # tasksets or tasks section of the configuration file

tasksets:
    # This section will contains a list of tasksets. All tasks within a
    # task set [TO BE DEFINED]
```

This is the top level structure of the benchmark configuration file.
As the model and grader definition often can be reused in other benchmark configuration files,
you can extract them into their own files, instead of adding those details in the different
benchmark configuration files. To do so, you would take the `models` or `graders` section and move
them into its own YAML file. In our example the files are `models.yml` and `graders.yml`.

Instead of having this:

```yaml
models:
    # This section contains a list of model definition

graders:
    # This section contains a list of grader definition
```

you could write this:

```yaml
includes:
  - ./models.yml
  - ./graders.yml
```

If the file paths are relative, they are applied to the location of the configuration file.

You can also mention several models or graders files, as long as the names of the models and graders
are distinct.
