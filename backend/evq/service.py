import sqlite3
from threading import RLock
from .core import Session, PadCreator, ModernCreator, TARIFFS
CREATORS = {'A': PadCreator, 'B': ModernCreator}
class Service:
    def __init__(self, db='evq.sqlite3'):
        self.db = str(db)
        self.lock = RLock()
        self.live = {}
        with sqlite3.connect(self.db) as c:
            c.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, station TEXT, status TEXT, target_kwh REAL, delivered_kwh REAL, tariff TEXT, cost_try REAL)')
    def stations(self):
        with self.lock:
            return [{'id': x, 'name': ('Wireless Pad' if x == 'A' else 'Smart Charger')+' '+x,
                     'status': 'busy' if any(s.station == x for s in self.live.values()) else 'available'} for x in CREATORS]
    def save(self, s):
        d = s.data()
        with sqlite3.connect(self.db) as c:
            c.execute('INSERT OR REPLACE INTO sessions VALUES (?,?,?,?,?,?,?)', tuple(d[k] for k in ('id','station','status','target_kwh','delivered_kwh','tariff','cost_try')))
        return d
    def start(self, station, kwh, tariff):
        with self.lock:
            if station not in CREATORS: raise ValueError('Unknown station')
            if tariff not in TARIFFS: raise ValueError('Unknown tariff')
            if isinstance(kwh,bool) or not isinstance(kwh,(int,float)) or not 0 < kwh <= 100: raise ValueError('Energy must be 0-100 kWh')
            if any(s.station == station for s in self.live.values()): raise ValueError('Station busy')
            s = Session(station,float(kwh),tariff,CREATORS[station]().create())
            self.live[s.id] = s
            return self.save(s)
    def change(self, id, action, kwh=None):
        with self.lock:
            if id not in self.live: raise KeyError('Active session not found')
            s = self.live[id]
            if action == 'advance':
                if isinstance(kwh,bool) or not isinstance(kwh,(int,float)): raise ValueError('Invalid kWh')
                s.state.advance(s,float(kwh))
            elif action == 'stop': s.state.stop(s)
            else: raise ValueError('Unknown action')
            if s.state.name != 'charging': self.live.pop(id)
            return self.save(s)
    def history(self):
        with sqlite3.connect(self.db) as c:
            c.row_factory = sqlite3.Row
            return [dict(r) for r in c.execute('SELECT * FROM sessions ORDER BY rowid DESC LIMIT 50')]
