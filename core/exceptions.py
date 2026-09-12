class ScrapingError(Exception):
    pass

class NotFoundError(ScrapingError):
    pass

class PriceNotFoundError(NotFoundError):
    """Custom exception raised when a price cannot be found for a bicycle reference."""
    pass

class ReferenceNotFoundError(NotFoundError):
    pass

class InvalidFormError(ScrapingError):
    pass

class CloudflareChallengeError(ScrapingError):
    pass