# Migration Plan: Pydantic v1 to v2

## Overview
This document outlines a step-by-step plan for migrating HYDROLIB-core from Pydantic v1 to Pydantic v2. The project is currently using Pydantic v2.5 as a dependency but is still using the v1 compatibility layer (`pydantic.v1`) throughout the codebase.

## Key Breaking Changes in Pydantic v2

1. **Validation System Changes**:
   - `validator` decorator is replaced with `field_validator`
   - `root_validator` is replaced with `model_validator`
   - Different behavior and syntax for validators

2. **Field Changes**:
   - Different behavior for default values
   - Changes to field validation

3. **Config Changes**:
   - `Config` class is replaced with `model_config`
   - Different configuration options

4. **Type Annotation Changes**:
   - Changes to how types are handled
   - New features for type validation

5. **Error Handling Changes**:
   - Different error types and structures
   - Changes to validation error handling

## Migration Strategy

The migration will be performed in phases to ensure a smooth transition and to maintain compatibility with existing code. Each phase will focus on a specific aspect of the migration, with tests run after each phase to ensure that functionality is maintained.

### Phase 1: Preparation and Initial Setup

1. **Fix Direct Imports**:
   - Update the one file that imports directly from `pydantic` without the `.v1` namespace:
     - `hydrolib/core/dflowfm/mdu/legacy.py`

2. **Create a Compatibility Layer**:
   - Create a module that re-exports Pydantic v2 components with v1-compatible interfaces
   - This will help with the transition and allow for gradual migration

3. **Update Test Infrastructure**:
   - Ensure tests can run with both v1 and v2 code
   - Add tests specifically for the compatibility layer

### Phase 2: Core Model Migration

1. **Migrate BaseModel**:
   - Update `BaseModel` in `hydrolib/core/basemodel.py` to use Pydantic v2
   - Update the `Config` class to use `model_config`
   - Update validation logic to use the new validation system

2. **Migrate FileModel**:
   - Update `FileModel` and related classes to use Pydantic v2
   - Update validation logic to use the new validation system

3. **Run Core Tests**:
   - Run tests in `tests/test_basemodel/` to ensure that the core functionality works

### Phase 3: Validator Migration

1. **Create Helper Functions**:
   - Create helper functions to simplify the migration of validators
   - These functions should handle the differences between v1 and v2 validators

2. **Migrate Field Validators**:
   - Update all `validator` decorators to use `field_validator`
   - Update the validator functions to use the new syntax and behavior

3. **Migrate Root Validators**:
   - Update all `root_validator` decorators to use `model_validator`
   - Update the validator functions to use the new syntax and behavior

4. **Run Validator Tests**:
   - Run tests that exercise the validators to ensure they work correctly

### Phase 4: Field Migration

1. **Update Field Usage**:
   - Update all `Field` usage to use the new syntax and behavior
   - Pay special attention to default values and validation

2. **Run Field Tests**:
   - Run tests that exercise field definitions to ensure they work correctly

### Phase 5: Model Migration

1. **Migrate Model Classes**:
   - Update all model classes to use Pydantic v2
   - Update any model-specific validation logic

2. **Run Model Tests**:
   - Run tests for each model to ensure they work correctly

### Phase 6: Error Handling Migration

1. **Update Error Handling**:
   - Update error handling code to use the new error types and structures
   - Update validation error handling

2. **Run Error Handling Tests**:
   - Run tests that exercise error handling to ensure it works correctly

### Phase 7: Cleanup and Final Testing

1. **Remove Compatibility Layer**:
   - Remove the compatibility layer created in Phase 1
   - Update any remaining code to use Pydantic v2 directly

2. **Run All Tests**:
   - Run all tests to ensure that the migration is complete and everything works correctly

3. **Update Documentation**:
   - Update documentation to reflect the changes
   - Add notes about the migration for users of the library

## Test Files to Run After Each Phase

### Phase 1:
- `tests/test_basemodel/test_basemodel.py`
- `tests/test_basemodel/test_model_treet_raverser.py`

### Phase 2:
- `tests/test_basemodel/test_basemodel.py`
- `tests/test_basemodel/test_model_treet_raverser.py`
- `tests/test_model.py`

### Phase 3:
- All tests that use validators:
  - `tests/dflowfm/test_*.py`
  - `tests/dimr/test_*.py`
  - `tests/rr/test_*.py`

### Phase 4:
- All tests that use fields:
  - `tests/dflowfm/test_*.py`
  - `tests/dimr/test_*.py`
  - `tests/rr/test_*.py`

### Phase 5:
- All model tests:
  - `tests/dflowfm/test_*.py`
  - `tests/dimr/test_*.py`
  - `tests/rr/test_*.py`

### Phase 6:
- All tests that involve error handling:
  - `tests/dflowfm/test_*.py`
  - `tests/dimr/test_*.py`
  - `tests/rr/test_*.py`

### Phase 7:
- All tests:
  - `pytest`

## Conclusion

This migration plan provides a structured approach to migrating from Pydantic v1 to v2. By following this plan, the migration can be performed in a controlled manner, with tests run after each phase to ensure that functionality is maintained. This will help to minimize the risk of introducing bugs during the migration process.