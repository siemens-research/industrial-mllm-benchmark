<!--
    SPDX-FileCopyrightText: Copyright 2024 Siemens AG
    SPDX-License-Identifier: MIT
-->
# Industrial LLM Benchmark

## Adding a new taskset

To add a new task set, just go into the benchmark configuration file and into the section `tasksets`.

Add there a new YAML section like this:

```yaml
  - name: My New Taskset
    models: [model1, model2]
    system_prompts:
        # here you can add system prompts for each model as described in [Overview](overview.md)
    tasks:
        # here you add your list of tasks
```

The `name` of the taskset must be unique within the benchmark config file.

The models must at most contain the models defined in the `models` section.
You can mention fewer models, if you don't want to use them on default for all tasks.
This list of models will be used for tasks which have not specified which models they want to use.
Reworded: Only when a task has not defined which models he should use, this models list will be used.

The system prompts are behaving similiar to the models list. Those system prompts are only used,
when the task does not specify its own system prompt. But it seems to be a best practice to
define system prompts on the taskset level (aka here) instead for each task. (Except of course
there is a good reason for it.)

The tasks contains now a list of tasks, which contains the actual queries for the MLLM.
