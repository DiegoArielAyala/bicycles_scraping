class PriceNotFoundError(Exception):
    """Custom exception raised when a price cannot be found for a bicycle reference."""
    pass

class ReferenceNotFound(Exception):
    pass