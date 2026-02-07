import importlib.util
import sys
import unittest
from pathlib import Path


def _load_module_from_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    tests_root = Path(__file__).resolve().parent
    suite = unittest.TestSuite()

    for test_file in sorted(tests_root.rglob("test*.py")):
        if test_file.name == "__init__.py":
            continue
        module_name = "tests_" + str(test_file.relative_to(repo_root)).replace("\\", "_").replace("/", "_").replace(
            ".", "_"
        )
        module = _load_module_from_path(module_name, test_file)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
