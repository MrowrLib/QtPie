## 🐍 Python Style Guide for AI Assistant

### Auto-removal of unused imports on save
- The code formatter will automatically remove any unused imports when you save the file.
- This is IMPORTANT to remember, as it will affect how you write your code.
- You MUST use all imports in the code before saving the file.

### Imports
- Important: I have an auto-save formatter which REMOVES all imports that are not used,
  so please make sure to use all imports in the code before you save the file.
- Imports should be added to the top of the file, never within functions or classes.

### Project Structure
- Do NOT use `__init__.py` files anywhere in the project.
- Use explicit imports with full module paths instead of relying on `__init__.py` exports.
- Name files after their primary class or function, using snake_case.
- For interface files, use the pattern `{domain}_interface.py`.
- For implementations, use the pattern `{domain}_{implementation}.py`.

### Typing
- All functions and methods must use **explicit type hints** on parameters and return types.
- **Never** use `Any` or `Unknown`.
- **Never** create type aliases for primitives (e.g. `UserId = str` is disallowed).
- Use **type inference** for local variables where types are obvious.
- Use `X | Y` instead of `Union[X, Y]`, and `str | None` instead of `Optional[str]`.
- NEVER use `typing_extensions`, we are using Python 3.13+ and can use the latest features. Import from `typing` directly.

### Data Modeling
- Use `@dataclass` for small value types. Mutability is preferred (`frozen=False` by default).
- Consider `frozen=True` for immutable value types when appropriate.
- Prefer mutable classes over immutable ones for domain objects and services.
- Prefer `list`, `dict`, etc. **Always use built-in generics** (e.g. `list[str]`, not `List[str]`).

### Interfaces and Class Design
- Use `ABC` to define interfaces. Prefix all ABCs with `I`, e.g. `class IShape(ABC)`.
- All abstract methods must be explicitly marked with `@abstractmethod`.
- Prefer `@dataclass` for concrete implementations when possible.

### Method Visibility
- Methods not used externally should be private (prefix with `_`).
- All helper or internal methods should start with `_`.

### Logging
- Use the `logging` module. Add logging where helpful for tracing logic or state.

### Python Version
- Use **Python 3.13+**. Use modern syntax everywhere.

---

### ✅ Example

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)

class IAnimal(ABC):
    @abstractmethod
    def speak(self) -> str: ...

@dataclass
class Dog(IAnimal):
    name: str

    def speak(self) -> str:
        msg = f"{self.name} says woof"
        logging.info(msg)
        return msg

def greet(animal: IAnimal) -> str:
    return animal.speak()

dog = Dog(name="Fido")
print(greet(dog))
```
