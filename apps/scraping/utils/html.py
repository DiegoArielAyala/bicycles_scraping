import logging

logger = logging.getLogger(__name__)

def get_href(product_element):
    a_tag = product_element.find("a")
    if not a_tag or not a_tag.get("href"):
        return None
    bicycle_href = a_tag.get("href")
    logger.debug(
        "Bicycle href",
        extra={
            "event": "bicycle_href",
            "href": bicycle_href,
        },
    )
    return bicycle_href