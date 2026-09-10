"""Storage checks tolerate files removed by a running game's save cleanup."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import search_schedule

class StorageTest(unittest.TestCase):
    def test_vanished_temporary_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            job = root / 'runs/job'
            job.mkdir(parents=True)
            stable = job / 'stable'
            stable.write_bytes(b'1234')
            original = Path.stat
            def stat(path, *args, **kwargs):
                if path.name == 'vanished':
                    raise FileNotFoundError(path)
                return original(path, *args, **kwargs)
            with patch.object(search_schedule, 'ROOT', root), patch('search_schedule.os.walk', return_value=[(str(job), [], ['stable','vanished'])]), patch.object(Path, 'stat', stat):
                result = search_schedule.disk_usage(job)
            self.assertEqual(result['new_bytes'], 4)
            self.assertEqual(result['vanished_temporary_files'], 1)

    def test_permission_error_is_not_hidden(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            job = root / 'runs/job'
            job.mkdir(parents=True)
            original = Path.stat
            def stat(path, *args, **kwargs):
                if path.name == 'blocked':
                    raise PermissionError(path)
                return original(path, *args, **kwargs)
            with patch.object(search_schedule, 'ROOT', root), patch('search_schedule.os.walk', return_value=[(str(job), [], ['blocked'])]), patch.object(Path, 'stat', stat):
                with self.assertRaises(PermissionError):
                    search_schedule.disk_usage(job)

if __name__ == '__main__':
    unittest.main()
