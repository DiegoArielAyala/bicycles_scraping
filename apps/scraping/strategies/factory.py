from apps.scraping.strategies.biking_point import BikingPointStrategy
from apps.scraping.strategies.escapa import EscapaStrategy

STRATEGIES = {
    "biking_point": BikingPointStrategy,
    "escapa": EscapaStrategy
}

def strategy_factory(web):
    try:
        return STRATEGIES[web]()
    except KeyError:
        raise ValueError(f"Invalid web: {web}")