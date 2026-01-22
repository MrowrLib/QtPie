"""Tests for YAML format loading/saving."""

from pathlib import Path

from assertpy import assert_that
from forc2.domain import Collection, Environment, HttpMethod, KeyValue, Request, Workspace
from forc2.format import (
    load_collection,
    load_environment,
    load_request,
    load_workspace_config,
    save_collection,
    save_environment,
    save_request,
)


class TestLoadRequest:
    """Tests for loading requests from YAML."""

    def test_load_basic_request(self, tmp_path: Path) -> None:
        """Load a simple request with name, method, url."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("""
name: Get Users
method: GET
url: https://api.example.com/users
""")
        req = load_request(yaml_file)

        assert_that(req.name.value).is_equal_to("Get Users")
        assert_that(req.method.value).is_equal_to(HttpMethod.GET)
        assert_that(req.url.value).is_equal_to("https://api.example.com/users")

    def test_load_request_with_headers(self, tmp_path: Path) -> None:
        """Load a request with headers."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("""
name: Test
method: POST
url: https://api.example.com
headers:
  - key: Content-Type
    value: application/json
  - key: Authorization
    value: Bearer token123
""")
        req = load_request(yaml_file)

        assert_that(list(req.headers.value)).is_length(2)
        assert_that(req.headers.value[0].key).is_equal_to("Content-Type")
        assert_that(req.headers.value[0].value).is_equal_to("application/json")
        assert_that(req.headers.value[1].key).is_equal_to("Authorization")

    def test_load_request_with_query_params(self, tmp_path: Path) -> None:
        """Load a request with query parameters."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("""
name: Search
method: GET
url: https://api.example.com/search
query_params:
  - key: q
    value: hello
  - key: limit
    value: "10"
""")
        req = load_request(yaml_file)

        assert_that(list(req.query_params.value)).is_length(2)
        assert_that(req.query_params.value[0].key).is_equal_to("q")
        assert_that(req.query_params.value[0].value).is_equal_to("hello")

    def test_load_request_with_body(self, tmp_path: Path) -> None:
        """Load a request with body."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("""
name: Create User
method: POST
url: https://api.example.com/users
body: '{"name": "John"}'
""")
        req = load_request(yaml_file)

        assert_that(req.body.value).is_equal_to('{"name": "John"}')

    def test_load_request_uses_filename_as_name(self, tmp_path: Path) -> None:
        """If no name field, use filename."""
        yaml_file = tmp_path / "my-request.yaml"
        yaml_file.write_text("""
method: GET
url: https://example.com
""")
        req = load_request(yaml_file)

        assert_that(req.name.value).is_equal_to("my-request")


class TestLoadCollection:
    """Tests for loading collections from directories."""

    def test_load_empty_collection(self, tmp_path: Path) -> None:
        """Load a collection with just metadata."""
        coll_dir = tmp_path / "my-collection"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: My Collection\n")

        coll = load_collection(coll_dir)

        assert_that(coll.name.value).is_equal_to("My Collection")
        assert_that(list(coll.items.value)).is_empty()

    def test_load_collection_with_requests(self, tmp_path: Path) -> None:
        """Load a collection containing requests."""
        coll_dir = tmp_path / "api"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")
        (coll_dir / "get-users.yaml").write_text("""
name: Get Users
method: GET
url: /users
""")
        (coll_dir / "create-user.yaml").write_text("""
name: Create User
method: POST
url: /users
""")

        coll = load_collection(coll_dir)

        assert_that(coll.name.value).is_equal_to("API")
        assert_that(list(coll.items.value)).is_length(2)
        # Items are sorted alphabetically
        assert_that(coll.items.value[0].name.value).is_equal_to("Create User")
        assert_that(coll.items.value[1].name.value).is_equal_to("Get Users")

    def test_load_nested_collections(self, tmp_path: Path) -> None:
        """Load a collection with sub-collections."""
        root = tmp_path / "root"
        root.mkdir()
        (root / "_collection.yaml").write_text("name: Root\n")

        child = root / "child"
        child.mkdir()
        (child / "_collection.yaml").write_text("name: Child Collection\n")
        (child / "request.yaml").write_text("""
name: Nested Request
method: GET
url: /nested
""")

        coll = load_collection(root)

        assert_that(coll.name.value).is_equal_to("Root")
        assert_that(list(coll.items.value)).is_length(1)

        sub = coll.items.value[0]
        assert isinstance(sub, Collection)
        assert_that(sub.name.value).is_equal_to("Child Collection")
        assert_that(list(sub.items.value)).is_length(1)
        assert_that(sub.items.value[0].name.value).is_equal_to("Nested Request")

    def test_load_collection_uses_folder_name(self, tmp_path: Path) -> None:
        """If no _collection.yaml, use folder name."""
        coll_dir = tmp_path / "my-api"
        coll_dir.mkdir()

        coll = load_collection(coll_dir)

        assert_that(coll.name.value).is_equal_to("my-api")


class TestLoadFixtures:
    """Tests that load the actual fixtures."""

    def test_load_demo_api(self) -> None:
        """Load the demo-api fixtures."""
        fixtures = Path("examples/forc2/fixtures/demo-api/collections")
        if not fixtures.exists():
            return  # Skip if fixtures don't exist

        root = load_collection(fixtures)

        # Should have 4 sub-collections
        assert_that(list(root.items.value)).is_length(4)

        # Find the Users collection
        users = next((c for c in root.items.value if c.name.value == "Users"), None)
        assert users is not None
        assert isinstance(users, Collection)

        # Should have requests
        assert_that(list(users.items.value)).is_not_empty()

    def test_state_parent_set_on_load(self) -> None:
        """Loaded items have state_parent set correctly."""
        fixtures = Path("examples/forc2/fixtures/demo-api/collections")
        if not fixtures.exists():
            return

        root = load_collection(fixtures)

        # Sub-collections should have root as parent
        for item in root.items.value:
            assert_that(item.state_parent).is_same_as(root)

            # Nested items should have their collection as parent
            if isinstance(item, Collection):
                for sub in item.items.value:
                    assert_that(sub.state_parent).is_same_as(item)


class TestSaveRequest:
    """Tests for saving requests to YAML."""

    def test_save_basic_request(self, tmp_path: Path) -> None:
        """Save a simple request."""
        req = Request()
        req.name.value = "Get Users"
        req.method.value = HttpMethod.GET
        req.url.value = "https://api.example.com/users"

        yaml_file = tmp_path / "test.yaml"
        save_request(req, yaml_file)

        # Load it back
        loaded = load_request(yaml_file)
        assert_that(loaded.name.value).is_equal_to("Get Users")
        assert_that(loaded.method.value).is_equal_to(HttpMethod.GET)
        assert_that(loaded.url.value).is_equal_to("https://api.example.com/users")

    def test_save_request_with_headers(self, tmp_path: Path) -> None:
        """Save a request with headers."""
        req = Request()
        req.name.value = "Test"
        req.method.value = HttpMethod.POST
        req.url.value = "https://api.example.com"
        req.headers.append(KeyValue(key="Content-Type", value="application/json"))
        req.headers.append(KeyValue(key="Authorization", value="Bearer token"))

        yaml_file = tmp_path / "test.yaml"
        save_request(req, yaml_file)

        loaded = load_request(yaml_file)
        assert_that(list(loaded.headers.value)).is_length(2)
        assert_that(loaded.headers.value[0].key).is_equal_to("Content-Type")

    def test_save_request_with_body(self, tmp_path: Path) -> None:
        """Save a request with body."""
        req = Request()
        req.name.value = "Create"
        req.method.value = HttpMethod.POST
        req.url.value = "/create"
        req.body.value = '{"name": "test"}'

        yaml_file = tmp_path / "test.yaml"
        save_request(req, yaml_file)

        loaded = load_request(yaml_file)
        assert_that(loaded.body.value).is_equal_to('{"name": "test"}')


class TestSaveCollection:
    """Tests for saving collections to directories."""

    def test_save_empty_collection(self, tmp_path: Path) -> None:
        """Save an empty collection."""
        coll = Collection()
        coll.name.value = "My API"

        save_path = tmp_path / "my-api"
        save_collection(coll, save_path)

        # Should have created the directory and metadata
        assert_that(save_path.exists()).is_true()
        assert_that((save_path / "_collection.yaml").exists()).is_true()

        # Load it back
        loaded = load_collection(save_path)
        assert_that(loaded.name.value).is_equal_to("My API")

    def test_save_collection_with_requests(self, tmp_path: Path) -> None:
        """Save a collection with requests."""
        coll = Collection()
        coll.name.value = "Users API"

        req1 = coll.add_request("Get Users")
        req1.method.value = HttpMethod.GET
        req1.url.value = "/users"

        req2 = coll.add_request("Create User")
        req2.method.value = HttpMethod.POST
        req2.url.value = "/users"

        save_path = tmp_path / "users"
        save_collection(coll, save_path)

        # Load it back
        loaded = load_collection(save_path)
        assert_that(loaded.name.value).is_equal_to("Users API")
        assert_that(list(loaded.items.value)).is_length(2)

    def test_save_nested_collections(self, tmp_path: Path) -> None:
        """Save nested collections."""
        root = Collection()
        root.name.value = "Root"

        child = root.add_collection("Child")
        req = child.add_request("Nested Request")
        req.url.value = "/nested"

        save_path = tmp_path / "root"
        save_collection(root, save_path)

        # Load it back
        loaded = load_collection(save_path)
        assert_that(loaded.name.value).is_equal_to("Root")
        assert_that(list(loaded.items.value)).is_length(1)

        loaded_child = loaded.items.value[0]
        assert isinstance(loaded_child, Collection)
        assert_that(loaded_child.name.value).is_equal_to("Child")
        assert_that(list(loaded_child.items.value)).is_length(1)


class TestLoadEnvironment:
    """Tests for loading environments from YAML."""

    def test_load_basic_environment(self, tmp_path: Path) -> None:
        """Load a simple environment with name and variables."""
        yaml_file = tmp_path / "dev.yaml"
        yaml_file.write_text("""
name: Development
variables:
  - key: BASE_URL
    value: http://localhost:8000
  - key: API_KEY
    value: secret123
    secret: true
""")
        env = load_environment(yaml_file)

        assert_that(env.name.value).is_equal_to("Development")
        assert_that(list(env.variables.value)).is_length(2)
        assert_that(env.variables.value[0].key).is_equal_to("BASE_URL")
        assert_that(env.variables.value[0].value).is_equal_to("http://localhost:8000")
        assert_that(env.variables.value[0].secret).is_false()
        assert_that(env.variables.value[1].key).is_equal_to("API_KEY")
        assert_that(env.variables.value[1].secret).is_true()

    def test_load_environment_uses_filename_as_name(self, tmp_path: Path) -> None:
        """If no name field, use filename."""
        yaml_file = tmp_path / "production.yaml"
        yaml_file.write_text("""
variables:
  - key: URL
    value: https://api.example.com
""")
        env = load_environment(yaml_file)

        assert_that(env.name.value).is_equal_to("production")
        assert_that(env.filename.value).is_equal_to("production")

    def test_load_environment_empty(self, tmp_path: Path) -> None:
        """Load an empty environment file."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")

        env = load_environment(yaml_file)

        assert_that(env.name.value).is_equal_to("empty")
        assert_that(list(env.variables.value)).is_empty()


class TestLoadEnvironmentFixtures:
    """Tests that load the actual environment fixtures."""

    def test_load_demo_environments(self) -> None:
        """Load the demo-api environment fixtures."""
        fixtures = Path("examples/forc2/fixtures/demo-api/environments")
        if not fixtures.exists():
            return

        dev_env = load_environment(fixtures / "development.yaml")
        assert_that(dev_env.name.value).is_equal_to("Development")
        assert_that(list(dev_env.variables.value)).is_not_empty()

        prod_env = load_environment(fixtures / "production.yaml")
        assert_that(prod_env.name.value).is_equal_to("Production")


class TestSaveEnvironment:
    """Tests for saving environments to YAML."""

    def test_save_basic_environment(self, tmp_path: Path) -> None:
        """Save a simple environment."""
        env = Environment()
        env.name.value = "Test"
        env.variables.append(KeyValue(key="URL", value="http://localhost"))

        yaml_file = tmp_path / "test.yaml"
        save_environment(env, yaml_file)

        # Load it back
        loaded = load_environment(yaml_file)
        assert_that(loaded.name.value).is_equal_to("Test")
        assert_that(list(loaded.variables.value)).is_length(1)
        assert_that(loaded.variables.value[0].key).is_equal_to("URL")

    def test_save_environment_with_secrets(self, tmp_path: Path) -> None:
        """Save an environment with secret variables."""
        env = Environment()
        env.name.value = "Secrets"
        env.variables.append(KeyValue(key="PUBLIC", value="visible"))
        env.variables.append(KeyValue(key="SECRET", value="hidden", secret=True))

        yaml_file = tmp_path / "secrets.yaml"
        save_environment(env, yaml_file)

        loaded = load_environment(yaml_file)
        assert_that(loaded.variables.value[0].secret).is_false()
        assert_that(loaded.variables.value[1].secret).is_true()


class TestRoundTrip:
    """Test loading, modifying, and saving."""

    def test_load_modify_save(self, tmp_path: Path) -> None:
        """Load fixtures, modify, save, reload."""
        fixtures = Path("examples/forc2/fixtures/demo-api/collections")
        if not fixtures.exists():
            return

        # Load
        root = load_collection(fixtures)
        original_count = len(list(root.items.value))

        # Modify - add a new collection
        new_coll = root.add_collection("New Collection")
        new_req = new_coll.add_request("New Request")
        new_req.url.value = "https://example.com/new"

        # Save to temp
        save_path = tmp_path / "modified"
        save_collection(root, save_path)

        # Reload
        reloaded = load_collection(save_path)

        # Should have one more collection
        assert_that(list(reloaded.items.value)).is_length(original_count + 1)

        # Find our new collection
        new = next((c for c in reloaded.items.value if c.name.value == "New Collection"), None)
        assert new is not None


class TestLoadWorkspaceConfig:
    """Tests for loading workspace config from forc.yaml."""

    def test_load_workspace_config_with_name(self, tmp_path: Path) -> None:
        """Load workspace name from forc.yaml."""
        (tmp_path / "forc.yaml").write_text("name: My Workspace\n")

        workspace = Workspace()
        load_workspace_config(workspace, tmp_path)

        assert_that(workspace.name.value).is_equal_to("My Workspace")

    def test_load_workspace_config_with_active_environment(self, tmp_path: Path) -> None:
        """Load active_environment from forc.yaml."""
        (tmp_path / "forc.yaml").write_text("active_environment: Production\n")

        workspace = Workspace()
        load_workspace_config(workspace, tmp_path)

        assert_that(workspace.active_environment.value).is_equal_to("Production")

    def test_load_workspace_config_with_both_fields(self, tmp_path: Path) -> None:
        """Load both name and active_environment from forc.yaml."""
        (tmp_path / "forc.yaml").write_text("""
name: JSONPlaceholder API
active_environment: Development
""")

        workspace = Workspace()
        load_workspace_config(workspace, tmp_path)

        assert_that(workspace.name.value).is_equal_to("JSONPlaceholder API")
        assert_that(workspace.active_environment.value).is_equal_to("Development")

    def test_load_workspace_config_missing_file(self, tmp_path: Path) -> None:
        """No error when forc.yaml doesn't exist."""
        workspace = Workspace()
        workspace.name.value = "Original"
        workspace.active_environment.value = "Original Env"

        load_workspace_config(workspace, tmp_path)

        # Values should remain unchanged
        assert_that(workspace.name.value).is_equal_to("Original")
        assert_that(workspace.active_environment.value).is_equal_to("Original Env")

    def test_load_workspace_config_empty_file(self, tmp_path: Path) -> None:
        """No error when forc.yaml is empty."""
        (tmp_path / "forc.yaml").write_text("")

        workspace = Workspace()
        workspace.name.value = "Original"

        load_workspace_config(workspace, tmp_path)

        # Value should remain unchanged
        assert_that(workspace.name.value).is_equal_to("Original")

    def test_load_workspace_config_partial_fields(self, tmp_path: Path) -> None:
        """Only specified fields are updated."""
        (tmp_path / "forc.yaml").write_text("name: New Name\n")

        workspace = Workspace()
        workspace.active_environment.value = "Should Stay"

        load_workspace_config(workspace, tmp_path)

        assert_that(workspace.name.value).is_equal_to("New Name")
        assert_that(workspace.active_environment.value).is_equal_to("Should Stay")


class TestLoadWorkspaceConfigFixtures:
    """Tests that load the actual workspace config fixtures."""

    def test_load_demo_api_workspace_config(self) -> None:
        """Load the demo-api forc.yaml fixture."""
        fixtures = Path("examples/forc2/fixtures/demo-api")
        if not fixtures.exists():
            return

        workspace = Workspace()
        load_workspace_config(workspace, fixtures)

        assert_that(workspace.name.value).is_equal_to("JSONPlaceholder API")
        assert_that(workspace.active_environment.value).is_equal_to("Production")
