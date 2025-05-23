## 🧪 Python Testing Style Guide

### Assertion Framework

- Use **assertpy** for all assertions in tests for better readability and error messages.
- The only exception is for `None` checks, where standard Python assertions should be used:
  - Use `assert x is None` for checking if something is `None`
  - Use `assert x is not None` for checking if something is not `None`
- For all other assertions, use assertpy's fluent API:
  - `assert_that(value).is_equal_to(expected)`
  - `assert_that(value).is_true()` / `assert_that(value).is_false()`
  - `assert_that(value).is_instance_of(type)`
  - `assert_that(collection).contains(item)`
  - `assert_that(collection).does_not_contain(item)`
  - `assert_that(collection).is_empty()`
  - `assert_that(collection).is_not_empty()`
  - `assert_that(collection).is_length(expected_length)`
  - `assert_that(collection).extracting('attribute').contains(value)`

### Test Structure

- Use pytest for all tests.
- Organize tests in classes named `Test{ClassName}` for the class being tested.
- Name test methods with `test_` prefix followed by the method or functionality being tested.
- Include docstrings for all test methods explaining what is being tested.
- Follow the Arrange-Act-Assert pattern in test methods:
  ```python
  def test_something(self) -> None:
      # Arrange
      obj = SomeClass()
      
      # Act
      result = obj.some_method()
      
      # Assert
      assert_that(result).is_equal_to(expected)
  ```

### Test Coverage

- Aim for high test coverage, especially for domain logic.
- Test both happy paths and edge cases.
- Include tests for error conditions and exception handling.
- Use parameterized tests for testing multiple similar cases.

### Example

```python
from assertpy import assert_that
from datetime import datetime

from myapp.domain.document import Document

class TestDocument:
    def test_create_document(self) -> None:
        """Test creating a document with default values."""
        # Arrange & Act
        doc = Document()
        
        # Assert
        assert doc.id is not None  # None check uses standard assertion
        assert_that(doc.name).is_equal_to("Untitled")
        assert_that(doc.content).is_empty()
        assert_that(doc.is_modified).is_false()
