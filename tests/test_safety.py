import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from smart_organizer.scanner import scan_directory
from smart_organizer.organizer import build_plan, execute_plan, undo, list_undo_logs, Strategy
from smart_organizer.duplicate_finder import find_duplicates

class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.target = self.root / 'target'
        self.logs = self.root / 'logs'

    def file(self, name, body):
        p = self.source / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
        return p

    def plan(self):
        return build_plan(scan_directory(str(self.source)), Strategy.BY_TYPE, str(self.target))

    def test_collisions_and_round_trip(self):
        self.file('a/same.txt', b'one')
        self.file('b/same.txt', b'two')
        existing = self.target / '文档/same.txt'
        existing.parent.mkdir(parents=True)
        existing.write_bytes(b'original')
        plan = self.plan()
        self.assertEqual(len({a.dst for a in plan.actions}), 2)
        log = execute_plan(plan, str(self.logs))
        self.assertEqual(existing.read_bytes(), b'original')
        self.assertEqual(undo(log), 2)
        self.assertEqual((self.source/'a/same.txt').read_bytes(), b'one')
        self.assertEqual((self.source/'b/same.txt').read_bytes(), b'two')
        self.assertEqual(list_undo_logs(str(self.logs)), [])

    def test_destination_created_after_preview(self):
        source = self.file('one.txt', b'one')
        plan = self.plan()
        dst = plan.actions[0].dst
        dst.parent.mkdir(parents=True)
        dst.write_bytes(b'new')
        with self.assertRaises(RuntimeError):
            execute_plan(plan, str(self.logs))
        self.assertEqual(source.read_bytes(), b'one')
        self.assertEqual(dst.read_bytes(), b'new')

    def test_partial_failure_has_recoverable_log(self):
        self.file('one.txt', b'one')
        self.file('two.txt', b'two')
        plan = self.plan()
        plan.actions[1].src.unlink()
        with self.assertRaises(RuntimeError):
            execute_plan(plan, str(self.logs))
        log, = list_undo_logs(str(self.logs))
        self.assertEqual(undo(log), 1)
        self.assertTrue(plan.actions[0].src.exists())

    def test_undo_conflict_can_be_retried(self):
        source = self.file('one.txt', b'one')
        log = execute_plan(self.plan(), str(self.logs))
        source.write_bytes(b'new user file')
        with self.assertRaises(RuntimeError):
            undo(log)
        self.assertEqual(source.read_bytes(), b'new user file')
        self.assertTrue(log.exists())
        source.unlink()
        self.assertEqual(undo(log), 1)
        self.assertEqual(source.read_bytes(), b'one')

    def test_undo_rejects_changed_content(self):
        self.file('one.txt', b'one')
        plan = self.plan()
        log = execute_plan(plan, str(self.logs))
        plan.actions[0].dst.write_bytes(b'changed')
        with self.assertRaises(RuntimeError):
            undo(log)
        self.assertEqual(plan.actions[0].dst.read_bytes(), b'changed')

    def test_pending_log_recovers_completed_move(self):
        self.file('one.txt', b'one')
        log = execute_plan(self.plan(), str(self.logs))
        data = json.loads(log.read_text())
        data['actions'][0]['status'] = 'pending'
        log.write_text(json.dumps(data))
        self.assertEqual(undo(log), 1)

    def test_copy_error_preserves_source(self):
        source = self.file('one.txt', b'one')
        plan = self.plan()
        with patch('smart_organizer.organizer.shutil.copyfileobj', side_effect=OSError('disk full')):
            with self.assertRaises(RuntimeError):
                execute_plan(plan, str(self.logs))
        self.assertEqual(source.read_bytes(), b'one')
        self.assertFalse(plan.actions[0].dst.exists())

    def test_duplicate_candidates_are_verified(self):
        self.file('a.bin', b'x'*8192+b'a')
        self.file('b.bin', b'x'*8192+b'b')
        self.file('c.bin', b'x'*8192+b'a')
        self.file('d.bin', b'x'*8192+b'longer')
        for quick in (True, False):
            groups = find_duplicates(scan_directory(str(self.source)), quick_mode=quick)
            self.assertEqual(len(groups), 1)
            self.assertEqual({f.name for f in next(iter(groups.values()))}, {'a.bin', 'c.bin'})

if __name__ == '__main__':
    unittest.main()
