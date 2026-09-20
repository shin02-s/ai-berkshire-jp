"""terminal_value.py の日本円対応回帰テスト。"""

import os
import subprocess
import sys
import unittest


_TOOL = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'tools', 'terminal_value.py')


def _run(args):
    return subprocess.run([sys.executable, _TOOL] + args, capture_output=True)


class TestJpyAudit(unittest.TestCase):

    def test_jpy_requires_explicit_risk_free_rate(self):
        proc = _run(['--locale', 'ja', 'audit', '--currency', 'JPY', '--r', '0.08',
                     '--roic', '0.20', '--g', '0.005,0.015,0.020'])
        self.assertEqual(proc.returncode, 1)
        self.assertIn('--rf', proc.stderr.decode('utf-8', 'replace'))

    def test_jpy_audit_accepts_explicit_rate(self):
        proc = _run(['--locale', 'ja', 'audit', '--currency', 'JPY', '--rf', '0.027',
                     '--r', '0.08', '--roic', '0.20', '--g', '0.005,0.015,0.020'])
        output = proc.stdout.decode('utf-8', 'replace')
        self.assertEqual(proc.returncode, 0, output)
        self.assertIn('評価前提の監査', output)
        self.assertIn('【合格】', output)

    def test_japanese_risk_placement_is_accepted(self):
        proc = _run([
            '--locale', 'ja', 'audit', '--currency', 'JPY', '--rf', '0.027',
            '--r', '0.08', '--roic', '0.20', '--g', '0.005,0.015,0.020',
            '--discrete-risks', '政策保有株:シナリオ,親子上場:確率',
        ])
        output = proc.stdout.decode('utf-8', 'replace')
        self.assertEqual(proc.returncode, 0, output)
        self.assertIn('政策保有株 → シナリオ', output)
        self.assertIn('親子上場 → 確率', output)

    def test_japanese_audit_failure_and_irr_output(self):
        failed = _run([
            '--locale', 'ja', 'audit', '--currency', 'JPY', '--rf', '0.02',
            '--r', '0.03', '--roic', '0.12', '--g', '0.00,0.01,0.02',
        ])
        failed_out = failed.stdout.decode('utf-8', 'replace')
        self.assertEqual(failed.returncode, 1)
        self.assertIn('【差し戻し】', failed_out)
        self.assertIn('⚠不足', failed_out)

        irr = _run([
            '--locale', 'ja', 'irr', '--profit', '1000', '--mcap', '10000',
            '--pe', '15', '--years', '10', '--payout', '0.02',
        ])
        irr_out = irr.stdout.decode('utf-8', 'replace')
        self.assertEqual(irr.returncode, 0, irr_out)
        self.assertIn('終値時価総額', irr_out)
        self.assertIn('IRR = +6.14%', irr_out)


if __name__ == '__main__':
    unittest.main()
