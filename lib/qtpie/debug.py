"""Debug logging for QtPie.

Enable debug logging:
    import logging
    logging.getLogger("qtpie").setLevel(logging.DEBUG)

Or via environment variable:
    QTPIE_DEBUG=1  # Sets all qtpie loggers to DEBUG level
"""

import logging
import os

# Create root qtpie logger - child loggers inherit from this
logger = logging.getLogger("qtpie")

# Check environment variable
if os.environ.get("QTPIE_DEBUG") in ("1", "true", "True"):
    # Configure basic logging format
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(name)s: %(message)s",
    )
    # Set qtpie root logger to DEBUG - all child loggers inherit this
    logger.setLevel(logging.DEBUG)
