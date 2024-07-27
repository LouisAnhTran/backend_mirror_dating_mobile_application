# logging_config.py

import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Log to console
    ]
)

logger = logging.getLogger(__name__)

