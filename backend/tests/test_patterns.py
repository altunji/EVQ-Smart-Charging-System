import tempfile, unittest
from pathlib import Path
from evq.core import PadCreator, PadAdapter, ModernCreator, Billing, StandardTariff, OffPeakTariff
from evq.service import Service
class TestPatterns(unittest.TestCase):
    def test_factory_adapter(self):
        p=PadCreator().create(); self.assertIsInstance(p,PadAdapter)
        p.start(); self.assertTrue(p.pad.on)
        p.stop(); self.assertFalse(p.pad.on)
        m=ModernCreator().create(); m.start(); self.assertTrue(m.on)
    def test_strategy(self):
        self.assertEqual(Billing(StandardTariff()).total(10),35)
        self.assertEqual(Billing(OffPeakTariff()).total(10),25)
    def test_state_and_database(self):
        with tempfile.TemporaryDirectory() as d:
            s=Service(Path(d)/'test.sqlite3')
            x=s.start('A',10,'standard')
            with self.assertRaises(ValueError): s.start('A',5,'standard')
            x=s.change(x['id'],'advance',4)
            self.assertEqual(x['status'],'charging')
            self.assertEqual(x['cost_try'],14)
            x=s.change(x['id'],'advance',10)
            self.assertEqual(x['status'],'completed')
            self.assertEqual(x['delivered_kwh'],10)
            self.assertEqual(len(s.history()),1)
            self.assertEqual(s.stations()[0]['status'],'available')
    def test_stop_and_invalid(self):
        with tempfile.TemporaryDirectory() as d:
            s=Service(Path(d)/'test.sqlite3')
            with self.assertRaises(ValueError): s.start('A',0,'standard')
            x=s.start('B',5,'off_peak')
            self.assertEqual(s.change(x['id'],'stop')['status'],'stopped')
            with self.assertRaises(KeyError): s.change(x['id'],'advance',1)
if __name__=='__main__': unittest.main()
