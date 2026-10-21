"""WSL startup recovery must be narrow and happen before experiment deployment."""
import errno
import unittest
from unittest.mock import MagicMock, patch
from test_audio import demo


class InteropTests(unittest.TestCase):
    def paths(self, kernel='microsoft-standard-WSL2', handler=False):
        def path(name):
            item=MagicMock()
            item.read_text.return_value=kernel
            item.is_file.return_value=True
            item.exists.return_value=handler if name.endswith('/WSLInterop') else True
            return item
        return path

    def test_ready_runtime_does_not_touch_registration(self):
        with patch.object(demo.subprocess,'run') as run, patch.object(demo,'Path') as path:
            demo.ensure_windows_runtime()
            run.assert_called_once()
            path.assert_not_called()

    def test_missing_wsl_handler_is_restored_and_reprobed(self):
        register=MagicMock()
        resolve=self.paths()
        with patch.object(demo.subprocess,'run',side_effect=[OSError(errno.ENOEXEC,'format'),None]) as run, patch.object(demo,'Path',side_effect=lambda n: register if n.endswith('/register') else resolve(n)):
            demo.ensure_windows_runtime()
            register.write_text.assert_called_once_with(':WSLInterop:M::MZ::/init:PF\n')
            self.assertEqual(run.call_count,2)

    def test_missing_node_is_not_treated_as_missing_handler(self):
        with patch.object(demo.subprocess,'run',side_effect=FileNotFoundError(errno.ENOENT,'missing')), patch.object(demo,'Path') as path:
            with self.assertRaises(FileNotFoundError):demo.ensure_windows_runtime()
            path.assert_not_called()

    def test_existing_handler_is_not_overwritten(self):
        with patch.object(demo.subprocess,'run',side_effect=OSError(errno.ENOEXEC,'format')) as run, patch.object(demo,'Path',side_effect=self.paths(handler=True)):
            with self.assertRaises(OSError):demo.ensure_windows_runtime()
            self.assertEqual(run.call_count,1)

    def test_non_wsl_kernel_is_not_changed(self):
        with patch.object(demo.subprocess,'run',side_effect=OSError(errno.ENOEXEC,'format')) as run, patch.object(demo,'Path',side_effect=self.paths(kernel='generic-linux')):
            with self.assertRaises(OSError):demo.ensure_windows_runtime()
            self.assertEqual(run.call_count,1)


if __name__=='__main__':unittest.main()