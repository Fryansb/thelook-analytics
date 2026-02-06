from abc import ABC, abstractmethod
from typing import Optional
from datetime import date
import random

from core.simulation_constants import MARKET_EVENT_PROBABILITY, EVENT_MULTIPLIERS


class MarketEvent(ABC):
    """Abstract base class for market events."""

    @abstractmethod
    def get_multiplier(self) -> float:
        """Return the impact multiplier for this event."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the event name."""
        pass


class ViralEvent(MarketEvent):
    """Product goes viral on social media."""

    def get_multiplier(self) -> float:
        return EVENT_MULTIPLIERS["viral"]

    def get_name(self) -> str:
        return "VIRAL"


class MarketingCampaignEvent(MarketEvent):
    """Successful marketing campaign."""

    def get_multiplier(self) -> float:
        return EVENT_MULTIPLIERS["marketing"]

    def get_name(self) -> str:
        return "MARKETING_CAMPAIGN"


class SiteDownEvent(MarketEvent):
    """Website downtime."""

    def get_multiplier(self) -> float:
        return EVENT_MULTIPLIERS["site_down"]

    def get_name(self) -> str:
        return "SITE_DOWN"


class LogisticsCrisisEvent(MarketEvent):
    """Logistics problems."""

    def get_multiplier(self) -> float:
        return EVENT_MULTIPLIERS["logistics"]

    def get_name(self) -> str:
        return "LOGISTICS_CRISIS"


class MarketEventFactory:
    """Factory for creating market events."""

    def __init__(self):
        self.events = {
            "viral": ViralEvent,
            "marketing": MarketingCampaignEvent,
            "site_down": SiteDownEvent,
            "logistics": LogisticsCrisisEvent,
        }

    def check_event(self, current_date: date) -> Optional[MarketEvent]:
        """Check if a market event occurs on the given date."""
        if random.random() < MARKET_EVENT_PROBABILITY:
            event_type = random.choice(list(self.events.keys()))
            return self.events[event_type]()
        return None
