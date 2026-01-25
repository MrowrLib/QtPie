"""Content Types router - endpoints returning various content types."""

import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, Response

router = APIRouter()

# Path to example files - resolved at module load time
EXAMPLE_FILES_DIR = Path(__file__).parent.parent / "example-files"

# Allowed filenames (whitelist approach for security)
ALLOWED_FILES = {
    "image.png",
    "doc.pdf",
    "doc-with-images.pdf",
    "sound.mp3",
    "homer-bushes.gif",
}


@router.get("/html/simple", response_class=HTMLResponse)
async def html_simple() -> str:
    """Return a simple HTML page."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple HTML Page</title>
</head>
<body>
    <h1>Hello from FastAPI!</h1>
    <p>This is a simple HTML response.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
        <li>Item 3</li>
    </ul>
</body>
</html>"""


@router.get("/html/styled", response_class=HTMLResponse)
async def html_styled() -> str:
    """Return an HTML page with CSS styling."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Styled HTML Page</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            margin-bottom: 1rem;
        }
        .badge {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            margin-right: 0.5rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>Styled Response</h1>
        <p>
            <span class="badge">FastAPI</span>
            <span class="badge">HTML</span>
            <span class="badge">CSS</span>
        </p>
        <table>
            <thead>
                <tr>
                    <th>Property</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Content-Type</td>
                    <td>text/html</td>
                </tr>
                <tr>
                    <td>Framework</td>
                    <td>FastAPI</td>
                </tr>
                <tr>
                    <td>Status</td>
                    <td>200 OK</td>
                </tr>
            </tbody>
        </table>
    </div>
</body>
</html>"""


@router.get("/xml/simple")
async def xml_simple() -> Response:
    """Return a simple XML response."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<response>
    <status>success</status>
    <message>Hello from FastAPI XML endpoint</message>
    <data>
        <item id="1">
            <name>First Item</name>
            <value>100</value>
        </item>
        <item id="2">
            <name>Second Item</name>
            <value>200</value>
        </item>
        <item id="3">
            <name>Third Item</name>
            <value>300</value>
        </item>
    </data>
    <metadata>
        <timestamp>2024-01-15T12:00:00Z</timestamp>
        <version>1.0</version>
    </metadata>
</response>"""
    return Response(content=xml_content, media_type="application/xml")


@router.get("/text/plain")
async def text_plain() -> Response:
    """Return a plain text response."""
    text_content = """Hello from FastAPI!

This is a plain text response.
No HTML, no JSON, just plain text.

Some example data:
- Name: Test API
- Version: 1.0.0
- Status: Running

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
"""
    return Response(content=text_content, media_type="text/plain")


@router.get("/json/detailed")
async def json_detailed() -> dict[str, Any]:
    """Return a detailed JSON response with nested structure."""
    return {
        "status": "success",
        "data": {
            "user": {
                "id": 12345,
                "name": "John Doe",
                "email": "john@example.com",
                "roles": ["admin", "user"],
            },
            "settings": {
                "theme": "dark",
                "notifications": True,
                "language": "en",
            },
            "stats": {
                "loginCount": 42,
                "lastLogin": "2024-01-15T10:30:00Z",
                "createdAt": "2023-06-01T08:00:00Z",
            },
        },
        "meta": {
            "requestId": "abc-123-xyz",
            "processingTime": "12ms",
        },
    }


@router.get("/files/{filename}")
async def get_file(filename: str) -> FileResponse:
    """Serve a file from the example-files directory.

    Security: Only allows files from a whitelist, no path traversal possible.
    """
    # Security: reject any path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename: path traversal not allowed",
        )

    # Security: only allow alphanumeric, dash, underscore, and dot
    if not re.match(r"^[\w\-\.]+$", filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename: contains disallowed characters",
        )

    # Security: check against whitelist
    if filename not in ALLOWED_FILES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found. Available files: {sorted(ALLOWED_FILES)}",
        )

    file_path = EXAMPLE_FILES_DIR / filename

    # Final safety check: ensure resolved path is within example-files
    try:
        file_path = file_path.resolve()
        expected_dir = EXAMPLE_FILES_DIR.resolve()
        if not str(file_path).startswith(str(expected_dir)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path",
            )
    except (OSError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path",
        ) from None

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {filename}",
        )

    return FileResponse(file_path, filename=filename)


@router.get("/files")
async def list_files() -> dict[str, Any]:
    """List available files that can be downloaded."""
    return {
        "available_files": sorted(ALLOWED_FILES),
        "endpoint": "/content/files/{filename}",
    }
