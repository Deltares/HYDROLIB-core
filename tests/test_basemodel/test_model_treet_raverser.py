from typing import Any, List, Optional

import pytest

from hydrolib.core.basemodel import BaseModel, ModelTreeTraverser


# Define test models
class SimpleModel(BaseModel):
    name: str
    value: int


class NestedModel(BaseModel):
    name: str
    child: Optional[SimpleModel] = None


class ModelWithList(BaseModel):
    name: str
    children: List[SimpleModel] = []


class ComplexModel(BaseModel):
    name: str
    nested: Optional[NestedModel] = None
    items: List[SimpleModel] = []
    mixed_items: List[Any] = []


@pytest.fixture
def simple_model():
    return SimpleModel(name="simple", value=42)


@pytest.fixture
def nested_model():
    return NestedModel(name="parent", child=SimpleModel(name="child", value=10))


@pytest.fixture
def model_with_list():
    return ModelWithList(
        name="list_parent",
        children=[
            SimpleModel(name="child1", value=1),
            SimpleModel(name="child2", value=2),
            SimpleModel(name="child3", value=3),
        ],
    )


@pytest.fixture
def complex_model():
    return ComplexModel(
        name="complex",
        nested=NestedModel(
            name="nested_parent", child=SimpleModel(name="nested_child", value=5)
        ),
        items=[
            SimpleModel(name="item1", value=10),
            SimpleModel(name="item2", value=20),
        ],
        mixed_items=[
            SimpleModel(name="mixed1", value=30),
            "not_a_model",
            NestedModel(
                name="mixed_nested", child=SimpleModel(name="deep_child", value=40)
            ),
            42,
        ],
    )


# Tests for basic traversal functionality
def test_traverse_simple_model(simple_model):
    """Test traversal of a simple model with no children."""
    # Count the number of models visited

    def count_visit(model: BaseModel, count: int) -> int:
        return count + 1

    traverser = ModelTreeTraverser[int](post_traverse_func=count_visit)

    result = traverser.traverse(simple_model, 0)

    # Only the simple model itself should be visited
    assert result == 1


def test_traverse_nested_model(nested_model):
    """Test traversal of a nested model."""

    # Collect model names during traversal
    def collect_name(model: BaseModel, names: List[str]) -> List[str]:
        if hasattr(model, "name"):
            names.append(model.name)
        return names

    traverser = ModelTreeTraverser[List[str]](post_traverse_func=collect_name)

    result = traverser.traverse(nested_model, [])

    # Both parent and child should be visited
    assert len(result) == 2
    assert "parent" in result
    assert "child" in result


def test_traverse_model_with_list(model_with_list):
    """Test traversal of a model with a list of child models."""

    # Sum the values of all models
    def sum_values(model: BaseModel, total: int) -> int:
        if hasattr(model, "value"):
            return total + model.value
        return total

    traverser = ModelTreeTraverser[int](post_traverse_func=sum_values)

    result = traverser.traverse(model_with_list, 0)

    # Sum should be 1 + 2 + 3 = 6
    assert result == 6


def test_traverse_complex_model(complex_model):
    """Test traversal of a complex model with nested structures and mixed content."""

    # Count all BaseModel instances
    def count_models(model: BaseModel, count: int) -> int:
        return count + 1

    traverser = ModelTreeTraverser[int](post_traverse_func=count_models)

    result = traverser.traverse(complex_model, 0)

    # Complex model has 7 BaseModel instances in total:
    # 1. complex_model itself
    # 2. nested
    # 3. nested.child
    # 4. items[0]
    # 5. items[1]
    # 6. mixed_items[0]
    # 7. mixed_items[2] (NestedModel)
    # 8. mixed_items[2].child
    assert result == 8


def test_pre_traverse_function(nested_model):
    """Test that the pre_traverse_func is called before traversing children."""

    def pre_visit(model: BaseModel, order: List[str]) -> List[str]:
        if hasattr(model, "name"):
            order.append(f"pre:{model.name}")
        return order

    def post_visit(model: BaseModel, order: List[str]) -> List[str]:
        if hasattr(model, "name"):
            order.append(f"post:{model.name}")
        return order

    traverser = ModelTreeTraverser[List[str]](
        pre_traverse_func=pre_visit, post_traverse_func=post_visit
    )

    result = traverser.traverse(nested_model, [])

    assert result == ["pre:parent", "pre:child", "post:child", "post:parent"]


def test_post_traverse_function(model_with_list):
    """Test that the post_traverse_func is called after traversing children."""

    # Track traversal order with depth
    class TraversalState:
        def __init__(self):
            self.depth = 0
            self.log = []

    def pre_visit(model: BaseModel, state: TraversalState) -> TraversalState:
        if hasattr(model, "name"):
            state.depth += 1
            state.log.append(f"enter:{model.name} at depth {state.depth}")
        return state

    def post_visit(model: BaseModel, state: TraversalState) -> TraversalState:
        if hasattr(model, "name"):
            state.log.append(f"exit:{model.name} at depth {state.depth}")
            state.depth -= 1
        return state

    traverser = ModelTreeTraverser[TraversalState](
        pre_traverse_func=pre_visit, post_traverse_func=post_visit
    )

    state = TraversalState()
    result = traverser.traverse(model_with_list, state)

    # Check that depth increases and decreases correctly
    assert result.log[0].startswith("enter:list_parent at depth 1")
    assert result.log[-1].startswith("exit:list_parent at depth 1")

    # Check that all children are visited between parent enter and exit
    child_entries = [log for log in result.log if "child" in log]
    assert len(child_entries) == 6  # 3 children, each with enter and exit

    # Check final depth is back to 0
    assert result.depth == 0


def test_empty_model():
    """Test traversal of an empty model."""

    class EmptyModel(BaseModel):
        pass

    empty = EmptyModel()

    # Count visits
    def count_visit(model: BaseModel, count: int) -> int:
        return count + 1

    traverser = ModelTreeTraverser[int](post_traverse_func=count_visit)

    result = traverser.traverse(empty, 0)

    # Only the empty model itself should be visited
    assert result == 1


def test_none_functions():
    """Test traversal with None functions."""
    model = SimpleModel(name="test", value=1)

    # Create traverser with no functions
    traverser = ModelTreeTraverser[int]()

    # Should not raise any errors
    result = traverser.traverse(model, 0)

    # Accumulator should be unchanged
    assert result == 0


def test_accumulator_transformation():
    """Test that the accumulator can be transformed during traversal."""
    model = ModelWithList(
        name="parent",
        children=[
            SimpleModel(name="child1", value=1),
            SimpleModel(name="child2", value=2),
        ],
    )

    # Transform accumulator from list to dict
    def list_to_dict(model: BaseModel, acc: Any) -> Any:
        if isinstance(acc, list) and hasattr(model, "name"):
            # Convert list to dict on first model
            return {model.name: 1}
        elif isinstance(acc, dict) and hasattr(model, "name"):
            # Add to dict for subsequent models
            acc[model.name] = len(acc) + 1
        return acc

    traverser = ModelTreeTraverser[Any](post_traverse_func=list_to_dict)

    result = traverser.traverse(model, [])

    # Result should be a dict with all model names
    assert isinstance(result, dict)
    assert len(result) == 3
    assert "parent" in result
    assert "child1" in result
    assert "child2" in result
