"""Snapshot invariants; optionally reconcile against the supplied processed CSVs."""
import csv
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / 'assets/data' / f'{name}.json').read_text(encoding='utf-8'))


class DashboardIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.k = read('overview_kpis')
        cls.cases = read('flagged_cases')
        cls.index = read('cases_index')

    def test_disjoint_complete_queue(self):
        counts = Counter(c['severity'] for c in self.cases)
        self.assertEqual(len(self.cases), self.k['flaggedCount'])
        self.assertEqual(len({c['id'] for c in self.cases}), len(self.cases))
        for severity, field in [('critical', 'criticalCount'), ('high', 'highCount'), ('med', 'medCount')]:
            self.assertEqual(counts[severity], self.k[field])
        self.assertEqual(sum(counts.values()) + self.k['lowCount'], self.k['totalScannedWorks'])
        for c in self.cases:
            self.assertTrue(any(c['flags'][f] for f in ['flag_delay','flag_amount','flag_mp_drift','iso_flag']))
            self.assertEqual(self.index[c['id']], c)

    def test_mirrors(self):
        for p in (ROOT/'assets/data').glob('*.json'):
            self.assertEqual(p.read_bytes(), (ROOT/'screens/assets/data'/p.name).read_bytes())

    def test_retired_detector_absent_from_exports(self):
        for p in (ROOT/'assets/data').glob('*.json'):
            text = p.read_text(encoding='utf-8').lower()
            self.assertNotIn('flag_round_number', text)
            self.assertNotIn('benford', text)

    @unittest.skipUnless(os.environ.get('NIDHI_PROCESSED_DIR'), 'Processed CSV source not supplied')
    def test_source_reconciliation(self):
        source = Path(os.environ['NIDHI_PROCESSED_DIR'])/'validation_results.csv'
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), self.k['provenance']['sha256'])
        with source.open(encoding='utf-8') as f:
            real = [r for r in csv.DictReader(f) if r['is_synthetic'] == '0']
        queue = [r for r in real if any(r[k] == 'True' for k in ['flag_delay','flag_amount','flag_mp_drift','iso_flag'])]
        self.assertEqual(len(real), self.k['totalScannedWorks'])
        self.assertEqual(len(queue), self.k['flaggedCount'])
        self.assertEqual(sum(r['rule_any_flag']=='True' for r in real), self.k['ruleFlaggedCount'])
        self.assertEqual(round(sum(float(r['Sanction Amount ( ₹ )']) for r in queue)/1e7, 1), self.k['scrutinyExposureCr'])
        for case in self.cases:
            row = real[case['sourceRow']-1]
            for key in ['flag_delay','flag_amount','flag_mp_drift','iso_flag']:
                self.assertEqual(case['flags'][key], row[key] == 'True')
            self.assertEqual(case['sanctioned_raw'], float(row['Sanction Amount ( ₹ )']))


if __name__ == '__main__':
    unittest.main()
