"""Mock data for the test API."""

# Valid credentials and tokens
VALID_API_KEY = "sk_live_abc123def456"
VALID_API_KEY_PUBLIC = "pk_test_xyz789"
VALID_USERNAME = "admin"
VALID_PASSWORD = "secret123"
VALID_BEARER_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0"
    ".Gfx6VO9tcxwk6xqx9yYzSfebfeakZp5JYIgP_edcw_A"
)

# Mock users
USERS = [
    {
        "id": 1,
        "name": "John Doe",
        "username": "johndoe",
        "email": "john@example.com",
        "avatar": None,
    },
    {
        "id": 2,
        "name": "Jane Smith",
        "username": "janesmith",
        "email": "jane@example.com",
        "avatar": None,
    },
    {
        "id": 3,
        "name": "Bob Wilson",
        "username": "bobwilson",
        "email": "bob@example.com",
        "avatar": None,
    },
]

# Mock posts
POSTS = [
    {
        "id": 1,
        "userId": 1,
        "title": "Getting Started with REST APIs",
        "body": "REST APIs are a powerful way to build web services...",
    },
    {
        "id": 2,
        "userId": 1,
        "title": "Understanding HTTP Methods",
        "body": "HTTP methods like GET, POST, PUT, DELETE each have specific purposes...",
    },
    {
        "id": 3,
        "userId": 2,
        "title": "API Authentication Best Practices",
        "body": "Securing your API is crucial for protecting user data...",
    },
]

# Mock comments
COMMENTS = [
    {"id": 1, "postId": 1, "name": "Alice", "email": "alice@example.com", "body": "Great article!"},
    {"id": 2, "postId": 1, "name": "Bob", "email": "bob@example.com", "body": "Very helpful, thanks!"},
    {"id": 3, "postId": 1, "name": "Charlie", "email": "charlie@example.com", "body": "I learned a lot from this."},
    {"id": 4, "postId": 2, "name": "Diana", "email": "diana@example.com", "body": "Clear explanation!"},
    {"id": 5, "postId": 2, "name": "Eve", "email": "eve@example.com", "body": "Could you elaborate on PUT vs PATCH?"},
    {"id": 6, "postId": 3, "name": "Frank", "email": "frank@example.com", "body": "Security is so important!"},
]

# User profile for bearer token auth
CURRENT_USER_PROFILE = {
    "id": 1,
    "name": "John Doe",
    "username": "johndoe",
    "email": "john@example.com",
    "role": "admin",
    "created_at": "2024-01-15T10:30:00Z",
}

# Secure data (for API key auth)
SECURE_DATA = {
    "message": "This is secure data",
    "secret_value": 42,
    "items": ["confidential", "private", "restricted"],
}

# Public data (for API key query param auth)
PUBLIC_DATA = {
    "message": "This is public data",
    "items": ["open", "accessible", "shared"],
}
