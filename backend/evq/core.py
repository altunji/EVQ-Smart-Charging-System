from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import uuid4

# Adapter: Target, Adaptee, Adapter
class ChargerPort(ABC):
    @abstractmethod
    def start(self): ...
    @abstractmethod
    def stop(self): ...
class LegacyPad:
    def __init__(self): self.on = False
    def pad_enable(self): self.on = True
    def pad_disable(self): self.on = False
class PadAdapter(ChargerPort):
    def __init__(self, pad): self.pad = pad
    def start(self): self.pad.pad_enable()
    def stop(self): self.pad.pad_disable()
class ModernPort(ChargerPort):
    def __init__(self): self.on = False
    def start(self): self.on = True
    def stop(self): self.on = False

# Factory Method: Creator, ConcreteCreators
class ChargerCreator(ABC):
    @abstractmethod
    def create(self) -> ChargerPort: ...
class PadCreator(ChargerCreator):
    def create(self): return PadAdapter(LegacyPad())
class ModernCreator(ChargerCreator):
    def create(self): return ModernPort()

# Strategy: Strategy, ConcreteStrategies, Context
class Tariff(ABC):
    @abstractmethod
    def cost(self, energy): ...
class StandardTariff(Tariff):
    def cost(self, energy): return round(energy * 3.5, 2)
class OffPeakTariff(Tariff):
    def cost(self, energy): return round(energy * 2.5, 2)
class Billing:
    def __init__(self, strategy: Tariff): self.strategy = strategy
    def total(self, energy): return self.strategy.cost(energy)
TARIFFS = {'standard': StandardTariff, 'off_peak': OffPeakTariff}

# State: State, ConcreteStates, Context (Session)
class State(ABC):
    name = 'unknown'
    def advance(self, session, kwh): raise ValueError('Session is not charging')
    def stop(self, session): raise ValueError('Session is not charging')
class Charging(State):
    name = 'charging'
    def advance(self, session, kwh):
        if not 0 < kwh <= 100: raise ValueError('Invalid energy increment')
        session.delivered = round(min(session.target, session.delivered + kwh), 3)
        if session.delivered >= session.target:
            session.charger.stop()
            session.state = Completed()
    def stop(self, session):
        session.charger.stop()
        session.state = Stopped()
class Completed(State): name = 'completed'
class Stopped(State): name = 'stopped'
@dataclass
class Session:
    station: str
    target: float
    tariff: str
    charger: ChargerPort = field(repr=False)
    id: str = field(default_factory=lambda: str(uuid4()))
    delivered: float = 0
    state: State = field(default_factory=Charging, repr=False)
    def __post_init__(self): self.charger.start()
    def data(self):
        return {'id': self.id, 'station': self.station, 'target_kwh': self.target,
                'delivered_kwh': self.delivered, 'tariff': self.tariff,
                'status': self.state.name,
                'cost_try': Billing(TARIFFS[self.tariff]()).total(self.delivered)}
