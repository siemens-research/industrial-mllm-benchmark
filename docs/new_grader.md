<!--
    SPDX-FileCopyrightText: Copyright 2024 Siemens AG
    SPDX-License-Identifier: MIT
-->
# Industrial LLM Benchmark

Here I want to show two use cases for adding a new grader.
The first is to add a different configured `expected_answer` grader, the second
and more complex one is how to add a new custom grader.

## Modifying `expected_answer` grader

Similiar to either add the grader to you your benchmark, or when you have
externalized graders into their own file into such file.
Here is the `expected_answer` grader from our example benchmark:

```yaml
  expected_answer:
    description: "This judge checks if the answer is the expected one"
    implementation:
      language: python
      module: industrial_mllm_benchmark
      function: expected_answer
      args:
        grader_model: model1
        system_prompt: >
          Judge the similarity between the two sentences without considering formatting, spelling,
          or how the information is presented. Rate the similarity on a scale from 0 to 1.0,
          where 0 means the sentences do not contain the same information, 0.5 means they contain
          overlapping information, and 1.0 means the sentences contain the same information.
          Output only the score.
        user_prompt: >
          Sentence one: {actual_answer}
          Sentence two: {expected_answer}
```

* `expected_answer` is the unique name of this grader, it will contain all the necessary details.
  This grader will use an MLLM to verify if the original answer is compatible to the expected answer
  given the system prompt this grader will use.
* `description` is used only for display and documentation purposes and should describe what
  the grader does.
* Similiar to the models, we will jump over the `implementation` block. Keep it as it is, and
modify the `args`section.
    * `grader_model` is referring to an existing model out of the models section. This model will
    beused for grading.
    * `system_prompt` specifies the system prompt this grader will be used to compare the actual with
    the expected answer.
    * `user_prompt` will be expanded with the actual and expected answer.

## Adding new simple grader

Currently you have to implement your own grader in Python. Other languages might be supported later.
A python grader is just a function which might look like the following signature. I'm a bit
vague here, as the signature can indeed look different depending on the args you defined in the
`args` section of the grader definition.

```python
def contains_grader(
    ec: EvalContext,
    context: dict[str, Any],
    expected_answer: str,
    actual_answer: str
) -> float:
```

* The `EvalContext` is used for (error) reporting. See some of the example implementations about details.
* The context dictionary contains for example a map will all available models.
* The actual answer is the answer returned by the model on behalf of a task
* The expected answer is configured in the `grader` usage within a task.

If you want to use your own grader you have to create a python module in which this grader resides.
Let us assume you have checked out the industrial_mllm_benchmark and create a new folder called
`custom`. Inside this folder, you have a file called `my_graders.py` with the following python code inside:

```python
from typing import Any
import logging
from industrial_mllm_benchmark import ParseContext as EvalContext

logger = logging.getLogger(__name__)

def contains_grader(
    ec: EvalContext,
    context: dict[str, Any],
    expected_answer: str,
    actual_answer: str
) -> float:
    # if actual answer contains the expected answer return 1.0 (=pass)
    # otherwise return 0.0 (=fail)
    return 1.0 if expected_answer in actual_answer else 0.0
```

Then you would need to enter the following in the `graders` section of your benchmark:

```yaml
  my_contains_version:
    description: "The actual answer contains the expected answer"
    implementation:
      language: python
      module: custom.my_graders
      function: contains_grader
```

## Adding new complex grader

Looking at the `expected_answer` grader definition, we see that there is an `args` section which
is missing in our simple grader example. All those keys you define in the `args` section are passed
during execution of the grader function as parameters into the function. This will require
that the signature of this grader function is extended by the arguments.

In case of the `expected_answer` grader the signature looks like the following:

```python
def expected_answer(
    ec: EvalContext,
    context: dict[str, Any],
    expected_answer: str,
    actual_answer: str,
    grader_model: str,
    system_prompt: str,
    user_prompt: str
) -> float:
```
