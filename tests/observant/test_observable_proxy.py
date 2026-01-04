"""Tests for ObservableProxy."""

# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false
# pyright: reportCallIssue=false, reportAttributeAccessIssue=false, reportIndexIssue=false
# pyright: reportArgumentType=false, reportUnknownVariableType=false, reportUnknownLambdaType=false

from dataclasses import dataclass

from assertpy import assert_that
from observant import ObservableDict, ObservableList, ObservableProxy


@dataclass
class Breed:
    """A dog breed."""

    name: str
    origin: str


@dataclass
class Dog:
    """A dog with a name and breed."""

    name: str
    age: int
    breed: Breed


@dataclass
class Person:
    """A person with basic info."""

    name: str
    age: int


class TestObservableProxyBasics:
    """Test basic proxy operations."""

    def test_wrap_object(self) -> None:
        """Can wrap an object."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)
        assert_that(proxy).is_not_none()

    def test_get_field_returns_observable(self) -> None:
        """Accessing a field returns an Observable."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)

        name_obs = proxy.name
        assert_that(name_obs.get()).is_equal_to("Alice")

    def test_get_field_value(self) -> None:
        """Can get field value via Observable.get()."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)

        assert_that(proxy.name.get()).is_equal_to("Alice")
        assert_that(proxy.age.get()).is_equal_to(30)

    def test_set_field_via_observable(self) -> None:
        """Can set field value via Observable.set()."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)

        proxy.name.set("Bob")
        assert_that(proxy.name.get()).is_equal_to("Bob")
        assert_that(person.name).is_equal_to("Bob")

    def test_set_field_via_proxy(self) -> None:
        """Can set field value directly on proxy."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)

        proxy.name = "Bob"
        assert_that(proxy.name.get()).is_equal_to("Bob")
        assert_that(person.name).is_equal_to("Bob")

    def test_unwrap_returns_target(self) -> None:
        """unwrap() returns the original object."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)

        assert_that(proxy.unwrap()).is_same_as(person)

    def test_nonexistent_field_raises(self) -> None:
        """Accessing nonexistent field raises AttributeError."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)

        try:
            _ = proxy.nonexistent
            assert_that(False).is_true()  # Should not reach here
        except AttributeError as e:
            assert_that(str(e)).contains("nonexistent")

    def test_repr(self) -> None:
        """repr shows wrapped object."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)

        assert_that(repr(proxy)).contains("ObservableProxy")
        assert_that(repr(proxy)).contains("Person")


class TestObservableProxyCallbacks:
    """Test change callbacks."""

    def test_on_change_fires_on_set(self) -> None:
        """Callback fires when field is set."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)
        changes: list[str] = []

        proxy.on_change(lambda: changes.append("changed"))

        proxy.name.set("Bob")
        assert_that(changes).is_equal_to(["changed"])

    def test_on_change_fires_on_direct_set(self) -> None:
        """Callback fires when field is set directly."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)
        changes: list[str] = []

        proxy.on_change(lambda: changes.append("changed"))

        proxy.name = "Bob"
        assert_that(changes).is_equal_to(["changed"])

    def test_field_on_change_fires(self) -> None:
        """Field Observable callback fires."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)
        changes: list[str] = []

        proxy.name.on_change(lambda v: changes.append(f"name={v}"))

        proxy.name.set("Bob")
        assert_that(changes).is_equal_to(["name=Bob"])

    def test_multiple_callbacks(self) -> None:
        """Multiple callbacks all fire."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)
        results: list[int] = []

        proxy.on_change(lambda: results.append(1))
        proxy.on_change(lambda: results.append(2))

        proxy.name.set("Bob")
        assert_that(results).is_equal_to([1, 2])


class TestObservableProxyDirty:
    """Test dirty tracking."""

    def test_initially_not_dirty(self) -> None:
        """New proxy is not dirty."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)
        assert_that(bool(proxy.is_dirty)).is_false()

    def test_dirty_after_set(self) -> None:
        """Proxy becomes dirty after field set."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)

        proxy.name.set("Bob")
        assert_that(bool(proxy.is_dirty)).is_true()

    def test_dirty_after_direct_set(self) -> None:
        """Proxy becomes dirty after direct set."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)

        # Access field first to create Observable
        _ = proxy.name.get()
        proxy.name = "Bob"
        assert_that(bool(proxy.is_dirty)).is_true()

    def test_reset_dirty_clears(self) -> None:
        """reset_dirty marks as clean."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)

        proxy.name.set("Bob")
        assert_that(bool(proxy.is_dirty)).is_true()

        proxy.reset_dirty()
        assert_that(bool(proxy.is_dirty)).is_false()

    def test_dirty_after_reset_and_change(self) -> None:
        """After reset, new changes make dirty again."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)

        proxy.name.set("Bob")
        proxy.reset_dirty()

        proxy.age.set(31)
        assert_that(bool(proxy.is_dirty)).is_true()

    def test_dirty_fields_list(self) -> None:
        """dirty_fields returns list of dirty field names."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)

        proxy.name.set("Bob")
        assert_that(proxy.dirty_fields).contains("name")
        assert_that(proxy.dirty_fields).does_not_contain("age")

    def test_is_dirty_is_observable(self) -> None:
        """is_dirty can be subscribed to."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person)
        dirty_states: list[bool] = []

        proxy.is_dirty.on_change(lambda d: dirty_states.append(d))

        proxy.name.set("Bob")  # clean -> dirty
        proxy.age.set(31)  # stays dirty
        proxy.reset_dirty()  # dirty -> clean

        assert_that(dirty_states).is_equal_to([True, False])


class TestObservableProxyNested:
    """Test nested object handling."""

    def test_nested_field_returns_proxy(self) -> None:
        """Accessing nested object returns ObservableProxy."""
        breed = Breed("Labrador", "Canada")
        dog = Dog("Buddy", 5, breed)
        proxy = ObservableProxy(dog)

        breed_proxy = proxy.breed
        assert_that(breed_proxy).is_instance_of(ObservableProxy)

    def test_nested_field_access(self) -> None:
        """Can access nested object fields."""
        breed = Breed("Labrador", "Canada")
        dog = Dog("Buddy", 5, breed)
        proxy = ObservableProxy(dog)

        assert_that(proxy.breed.name.get()).is_equal_to("Labrador")
        assert_that(proxy.breed.origin.get()).is_equal_to("Canada")

    def test_nested_field_set(self) -> None:
        """Can set nested object fields."""
        breed = Breed("Labrador", "Canada")
        dog = Dog("Buddy", 5, breed)
        proxy = ObservableProxy(dog)

        proxy.breed.name.set("Golden Retriever")
        assert_that(proxy.breed.name.get()).is_equal_to("Golden Retriever")
        assert_that(breed.name).is_equal_to("Golden Retriever")

    def test_nested_change_fires_parent_callback(self) -> None:
        """Nested changes fire parent callback."""
        breed = Breed("Labrador", "Canada")
        dog = Dog("Buddy", 5, breed)
        proxy = ObservableProxy(dog)
        changes: list[str] = []

        proxy.on_change(lambda: changes.append("dog_changed"))

        proxy.breed.name.set("Golden Retriever")
        assert_that(changes).is_equal_to(["dog_changed"])

    def test_nested_dirty_propagates_up(self) -> None:
        """Nested dirty state propagates to parent."""
        breed = Breed("Labrador", "Canada")
        dog = Dog("Buddy", 5, breed)
        proxy = ObservableProxy(dog)

        assert_that(bool(proxy.is_dirty)).is_false()

        proxy.breed.name.set("Golden Retriever")
        assert_that(bool(proxy.is_dirty)).is_true()
        assert_that(bool(proxy.breed.is_dirty)).is_true()

    def test_nested_reset_dirty(self) -> None:
        """Reset dirty clears nested dirty state."""
        breed = Breed("Labrador", "Canada")
        dog = Dog("Buddy", 5, breed)
        proxy = ObservableProxy(dog)

        proxy.breed.name.set("Golden Retriever")
        assert_that(bool(proxy.is_dirty)).is_true()

        proxy.reset_dirty()
        assert_that(bool(proxy.is_dirty)).is_false()
        assert_that(bool(proxy.breed.is_dirty)).is_false()

    def test_nested_dirty_fields(self) -> None:
        """dirty_fields includes nested proxy names."""
        breed = Breed("Labrador", "Canada")
        dog = Dog("Buddy", 5, breed)
        proxy = ObservableProxy(dog)

        proxy.breed.name.set("Golden Retriever")
        assert_that(proxy.dirty_fields).contains("breed")


@dataclass
class PersonWithCollections:
    """A person with list and dict fields."""

    name: str
    tags: list[str]
    metadata: dict[str, int]


class TestObservableProxyListField:
    """Test list field handling."""

    def test_list_field_returns_observable_list(self) -> None:
        """Accessing a list field returns ObservableList."""
        person = PersonWithCollections("Alice", ["admin", "user"], {"age": 30})
        proxy = ObservableProxy(person)

        tags = proxy.tags
        assert_that(tags).is_instance_of(ObservableList)

    def test_list_field_access(self) -> None:
        """Can access list items."""
        person = PersonWithCollections("Alice", ["admin", "user"], {"age": 30})
        proxy = ObservableProxy(person)

        assert_that(proxy.tags[0]).is_equal_to("admin")
        assert_that(len(proxy.tags)).is_equal_to(2)

    def test_list_field_modify(self) -> None:
        """Can modify list field."""
        person = PersonWithCollections("Alice", ["admin", "user"], {"age": 30})
        proxy = ObservableProxy(person)

        proxy.tags.append("moderator")
        assert_that(proxy.tags.to_list()).is_equal_to(["admin", "user", "moderator"])

    def test_list_field_dirty(self) -> None:
        """List modification marks proxy dirty."""
        person = PersonWithCollections("Alice", ["admin", "user"], {"age": 30})
        proxy = ObservableProxy(person)

        assert_that(bool(proxy.is_dirty)).is_false()
        proxy.tags.append("moderator")
        assert_that(bool(proxy.is_dirty)).is_true()
        assert_that(proxy.dirty_fields).contains("tags")

    def test_list_field_callback(self) -> None:
        """List modification fires proxy callback."""
        person = PersonWithCollections("Alice", ["admin", "user"], {"age": 30})
        proxy = ObservableProxy(person)
        changes: list[str] = []

        proxy.on_change(lambda: changes.append("changed"))
        proxy.tags.append("moderator")

        assert_that(changes).is_equal_to(["changed"])


class TestObservableProxyDictField:
    """Test dict field handling."""

    def test_dict_field_returns_observable_dict(self) -> None:
        """Accessing a dict field returns ObservableDict."""
        person = PersonWithCollections("Alice", ["admin"], {"age": 30})
        proxy = ObservableProxy(person)

        metadata = proxy.metadata
        assert_that(metadata).is_instance_of(ObservableDict)

    def test_dict_field_access(self) -> None:
        """Can access dict items."""
        person = PersonWithCollections("Alice", ["admin"], {"age": 30, "score": 100})
        proxy = ObservableProxy(person)

        assert_that(proxy.metadata["age"]).is_equal_to(30)
        assert_that(len(proxy.metadata)).is_equal_to(2)

    def test_dict_field_modify(self) -> None:
        """Can modify dict field."""
        person = PersonWithCollections("Alice", ["admin"], {"age": 30})
        proxy = ObservableProxy(person)

        proxy.metadata["score"] = 100
        assert_that(proxy.metadata.to_dict()).is_equal_to({"age": 30, "score": 100})

    def test_dict_field_dirty(self) -> None:
        """Dict modification marks proxy dirty."""
        person = PersonWithCollections("Alice", ["admin"], {"age": 30})
        proxy = ObservableProxy(person)

        assert_that(bool(proxy.is_dirty)).is_false()
        proxy.metadata["score"] = 100
        assert_that(bool(proxy.is_dirty)).is_true()
        assert_that(proxy.dirty_fields).contains("metadata")

    def test_dict_field_callback(self) -> None:
        """Dict modification fires proxy callback."""
        person = PersonWithCollections("Alice", ["admin"], {"age": 30})
        proxy = ObservableProxy(person)
        changes: list[str] = []

        proxy.on_change(lambda: changes.append("changed"))
        proxy.metadata["score"] = 100

        assert_that(changes).is_equal_to(["changed"])


class TestObservableProxyNoTracking:
    """Test with dirty tracking disabled."""

    def test_no_dirty_tracking(self) -> None:
        """Can disable dirty tracking."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person, dirty_tracking=False)

        try:
            _ = proxy.is_dirty
            assert_that(False).is_true()  # Should not reach here
        except RuntimeError as e:
            assert_that(str(e)).contains("not enabled")

    def test_works_without_dirty_tracking(self) -> None:
        """Proxy works fine without dirty tracking."""
        person = Person("Alice", 30)
        proxy = ObservableProxy(person, dirty_tracking=False)
        changes: list[str] = []

        proxy.on_change(lambda: changes.append("changed"))

        proxy.name.set("Bob")
        assert_that(proxy.name.get()).is_equal_to("Bob")
        assert_that(changes).is_equal_to(["changed"])
