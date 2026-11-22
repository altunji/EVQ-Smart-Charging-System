
import sqlite3
from contextlib import closing
from threading import RLock

from .core import Session, PadCreator, ModernCreator, TARIFFS


# Factory Method: creators for the supported charging stations
CREATORS = {
    'A': PadCreator,
    'B': ModernCreator
}


class Service:
    """Manage charging sessions, stations and SQLite persistence."""

    def __init__(self, db='evq.sqlite3'):
        self.db = str(db)
        self.lock = RLock()
        self.live = {}

        # Always close SQLite connections after database operations.
        with closing(sqlite3.connect(self.db)) as c, c:
            c.execute(
                'CREATE TABLE IF NOT EXISTS sessions ('
                'id TEXT PRIMARY KEY, '
                'station TEXT, '
                'status TEXT, '
                'target_kwh REAL, '
                'delivered_kwh REAL, '
                'tariff TEXT, '
                'cost_try REAL)'
            )

    def stations(self):
        """Return the availability of all charging stations."""
        with self.lock:
            return [
                {
                    'id': x,
                    'name': (
                        'Wireless Pad' if x == 'A'
                        else 'Smart Charger'
                    ) + ' ' + x,
                    'status': (
                        'busy'
                        if any(s.station == x for s in self.live.values())
                        else 'available'
                    )
                }
                for x in CREATORS
            ]

    def save(self, s):
        """Save or update a charging session in SQLite."""
        d = s.data()

        with closing(sqlite3.connect(self.db)) as c, c:
            c.execute(
                'INSERT OR REPLACE INTO sessions '
                'VALUES (?,?,?,?,?,?,?)',
                tuple(
                    d[k] for k in (
                        'id',
                        'station',
                        'status',
                        'target_kwh',
                        'delivered_kwh',
                        'tariff',
                        'cost_try'
                    )
                )
            )

        return d

    def start(self, station, kwh, tariff):
        """Start a new simulated charging session."""
        with self.lock:

            if station not in CREATORS:
                raise ValueError('Unknown station')

            if tariff not in TARIFFS:
                raise ValueError('Unknown tariff')

            if (
                isinstance(kwh, bool)
                or not isinstance(kwh, (int, float))
                or not 0 < kwh <= 100
            ):
                raise ValueError('Energy must be 0-100 kWh')

            if any(
                s.station == station
                for s in self.live.values()
            ):
                raise ValueError('Station busy')

            # Factory Method creates the selected charger controller.
            creator = CREATORS[station]()
            charger = creator.create()

            # State Pattern controls charging session transitions.
            s = Session(
                station,
                float(kwh),
                tariff,
                charger
            )

            self.live[s.id] = s

            return self.save(s)

    def change(self, id, action, kwh=None):
        """Advance or stop an active charging session."""
        with self.lock:

            if id not in self.live:
                raise KeyError('Active session not found')

            s = self.live[id]

            if action == 'advance':

                if (
                    isinstance(kwh, bool)
                    or not isinstance(kwh, (int, float))
                ):
                    raise ValueError('Invalid kWh')

                s.state.advance(s, float(kwh))

            elif action == 'stop':
                s.state.stop(s)

            else:
                raise ValueError('Unknown action')

            # Remove completed or stopped sessions from active memory.
            if s.state.name != 'charging':
                self.live.pop(id)

            return self.save(s)

    def history(self):
        """Read the latest 50 charging sessions from SQLite."""
        with closing(sqlite3.connect(self.db)) as c, c:
            c.row_factory = sqlite3.Row

            return [
                dict(r)
                for r in c.execute(
                    'SELECT * FROM sessions '
                    'ORDER BY rowid DESC LIMIT 50'
                )
            ]
