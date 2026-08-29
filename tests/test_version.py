import contextlib
import io
import tomllib
import unittest
from pathlib import Path

from solace import __version__
from solace.__main__ import build_parser


class VersionTests(unittest.TestCase):
    def test_human_readable_version(self):
        self.assertEqual(__version__, "0.2.0-alpha.1")

    def test_cli_version_uses_package_version(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as exit_info:
            build_parser().parse_args(["--version"])
        self.assertEqual(exit_info.exception.code, 0)
        self.assertEqual(output.getvalue().strip(), f"Solace {__version__}")

    def test_pyproject_reads_the_authoritative_package_version(self):
        project_root = Path(__file__).resolve().parents[1]
        metadata = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertNotIn("version", metadata["project"])
        self.assertIn("version", metadata["project"]["dynamic"])
        self.assertEqual(
            metadata["tool"]["setuptools"]["dynamic"]["version"]["attr"],
            "solace.__version__",
        )

    def test_python_target_is_exactly_3_12(self):
        project_root = Path(__file__).resolve().parents[1]
        metadata = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(metadata["project"]["requires-python"], ">=3.12,<3.13")


if __name__ == "__main__":
    unittest.main()
