<!--
    SPDX-FileCopyrightText: Copyright 2024 Siemens AG
    SPDX-License-Identifier: MIT
-->
# Industrial LLM Benchmark

## Adding a new task

To add a new task, just go into the benchmark configuration file and into the section `tasksets`
and there into that taskset you want to add your task to.

Add there a new YAML section like this:

```yaml
    - name: Basic Component Connections

      user_prompt:
        - image: images/datasheet.jpg
        - text: With which components is FD1771 connected? List only the component names without further explanation.

      graders:
        threshold: 0.8
        use:
          - name: expected_answer
            weight: 1
            answer: "Computer Interface, Floppy Disk Drive"

      metadata:
        task_type: information_extraction
        complexity: {input_amount: 2, domain_knowledge: 1, indirection: 1, multiplicity: 1}
        relevant_for:
          - electronics production
          - electronics product design
```

The `name` of the task must be unique within its taskset.

The `user_prompt` contains a list of prompt lines. The list in the specified order is then user prompt.
Each line must specify if it contains an `image` or an `text` prompt. If it is a image and the path
is relative, it resolved relative to the benchmark configuration file.
The user prompt is the same for any model this task is using.

The `graders` section specifies how the response of the MLLM with regard to the user prompt
should be graded.

The key `threshold` specifies a value between 0.0 and 1.0. When the combined weight of all grader
results is equal or higher then the threshold the answer of that model is treated as pass or success.
If it is lower it is failure. If during the evaluation of the grader an exception happens, it will be
reported as error.

The `use` section with the graders lists the graders which should be used and some configuration for them.
The name attribute is used to lookup this grader in the grader definitions.
The weight attribute indicates with what weight the result of this grader should go into the total result.
The answer section is the answer the grader should match the actual response against.

The `metadata` section will be passed as it is into the result file. It won't be inspected or used in any form
except to be copied into the result file. The idea is to annotate the task with your own categories, so
when you analyze the benchmark results, you can find those metadata in an conveninent place.

The above section is missing the following two sections:

* `models`: Here you could mention a list of models this task should use. If there is no such models definition,
it will look up the models section of its taskset.

* `system_prompts`: The same behaviour like the models section.

It seems to be best practive to NOT specify models and system_prompts on the task level. Only do this,
if the task should explicitly be treated differently then the other tasks of the taskset.
