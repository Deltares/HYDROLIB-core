# ModelTreeTraverser

## Overview

The `ModelTreeTraverser` is a powerful utility class in HYDROLIB-core that enables traversal of a model tree consisting of `BaseModel` objects. It provides a flexible way to execute custom functions during traversal, with control over which models to traverse and which functions to execute.

The traverser is designed to be generic, allowing for different types of accumulator objects to be passed through the traversal process. This accumulator can be used to collect information, build output values, or maintain state during traversal.

## Class Definition

```python
class ModelTreeTraverser(Generic[TAcc]):
    def __init__(
        self,
        should_traverse: Optional[Callable[[BaseModel, TAcc], bool]] = None,
        should_execute: Optional[Callable[[BaseModel, TAcc], bool]] = None,
        pre_traverse_func: Optional[Callable[[BaseModel, TAcc], TAcc]] = None,
        post_traverse_func: Optional[Callable[[BaseModel, TAcc], TAcc]] = None,
    ):
        # ...
```

Where:
- `TAcc` is a generic type parameter representing the accumulator type
- `should_traverse` is a function that determines whether to traverse to a given model
- `should_execute` is a function that determines whether to execute the traverse functions for a given model
- `pre_traverse_func` is a function executed before traversing into child models (top-down)
- `post_traverse_func` is a function executed after traversing into child models (bottom-up)

## Key Features

### Generic Accumulator

The `ModelTreeTraverser` uses a generic type parameter `TAcc` to define the type of accumulator that will be passed through the traversal. This allows for flexibility in what data is collected or maintained during traversal.

### Customizable Traversal Behavior

The traversal behavior can be customized through two predicate functions:

1. `should_traverse`: Determines whether to traverse to a given model. If not provided, all `BaseModel` objects will be traversed.
2. `should_execute`: Determines whether to execute the traverse functions for a given model. If not provided, traverse functions will be executed for all models.

### Pre and Post Traversal Functions

The traverser supports two types of traversal functions:

1. `pre_traverse_func`: Executed before traversing into child models, enabling top-down traversal.
2. `post_traverse_func`: Executed after traversing into child models, enabling bottom-up traversal.

Both functions receive the current model and accumulator as arguments and should return the (potentially modified) accumulator.

## Usage Examples

### Basic Usage

```python
from hydrolib.core.basemodel import ModelTreeTraverser, BaseModel


# Create a simple accumulator to count models
def count_models(model: BaseModel, count: int) -> int:
    return count + 1

# Create a traverser that counts all models
traverser = ModelTreeTraverser[int](
    post_traverse_func=count_models,
)

# Start traversal with an initial count of 0
total_models = traverser.traverse(root_model, 0)
print(f"Total models: {total_models}")
```

### Filtering Models

```python
from hydrolib.core.basemodel import ModelTreeTraverser, BaseModel, FileModel


# Only traverse FileModel objects
def is_file_model(model: BaseModel, acc: list) -> bool:
    return isinstance(model, FileModel)

# Collect all FileModel objects
def collect_file_model(model: BaseModel, models: list) -> list:
    models.append(model)
    return models

# Create a traverser that collects only FileModel objects
traverser = ModelTreeTraverser[list](
    should_traverse=is_file_model,
    should_execute=is_file_model,
    post_traverse_func=collect_file_model,
)

# Start traversal with an empty list
file_models = traverser.traverse(root_model, [])
```

### Complex Traversal with State

```python
from hydrolib.core.basemodel import ModelTreeTraverser, BaseModel, FileModel


# Define an accumulator type with state
class TraversalState:

    def __init__(self):
        self.depth = 0
        self.results = {}

# Pre-traversal function that increases depth
def enter_model(model: BaseModel, state: TraversalState) -> TraversalState:
    state.depth += 1
    return state

# Post-traversal function that decreases depth and records information
def exit_model(model: BaseModel, state: TraversalState) -> TraversalState:
    if isinstance(model, FileModel) and model.filepath is not None:
        state.results[str(model.filepath)] = {
            "depth": state.depth,
            "type": type(model).__name__,
        }
    state.depth -= 1
    return state

# Create a traverser with both pre and post functions
traverser = ModelTreeTraverser[TraversalState](
    pre_traverse_func=enter_model,
    post_traverse_func=exit_model,
)

# Start traversal with a new state object
state = TraversalState()
final_state = traverser.traverse(root_model, state)

# Access the collected results
for path, info in final_state.results.items():
    print(f"{path}: {info['type']} at depth {info['depth']}")
```

## Common Use Cases in HYDROLIB-core

The `ModelTreeTraverser` is used in several key areas of HYDROLIB-core:

1. **Generating Names**: Ensuring all models in a tree have valid file paths before saving.
2. **Saving Models**: Traversing the model tree to save each model to disk.
3. **Synchronizing File Paths**: Updating the save locations of child models when a parent model's path changes.

## Implementation Details

### Traversal Algorithm

The traversal algorithm is a depth-first search that:

1. Optionally executes the pre-traverse function on the current model
2. Iterates through all attributes of the current model
3. For each attribute that is a BaseModel or a list containing BaseModels, recursively traverses those models if the should_traverse predicate allows it
4. Optionally executes the post-traverse function on the current model after all children have been traversed

### Handling Lists and Nested Structures

The traverser automatically handles both direct BaseModel attributes and lists containing BaseModel objects. This allows it to work with the complex nested structures common in HYDROLIB-core models.

## Best Practices

1. **Keep Traverse Functions Pure**: Traverse functions should primarily modify the accumulator, not the models themselves, to maintain predictable behavior.
2. **Use Type Hints**: Always specify the accumulator type parameter to ensure type safety.
3. **Consider Performance**: For large model trees, be selective about which models to traverse using the should_traverse predicate.
4. **Handle Errors Gracefully**: Traverse functions should handle potential errors to prevent traversal from being interrupted.