#!/usr/bin/env python3
"""
Package validation script for spec-server.

This script validates the package structure, dependencies, and functionality
before distribution.
"""

import ast
import sys
from pathlib import Path
from typing import List


class PackageValidator:
    """Validates the spec-server package."""

    def __init__(self, project_root: Path):
        """Initialize validator with project root."""
        self.project_root = project_root
        self.src_dir = project_root / "src" / "spec_server"
        self.tests_dir = project_root / "tests"
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("🔍 Validating spec-server package...")

        # Structure validation
        self.validate_package_structure()
        self.validate_pyproject_toml()
        self.validate_source_code()
        self.validate_tests()
        self.validate_documentation()
        self.validate_scripts()

        # Functional validation
        self.validate_imports()
        self.validate_entry_points()

        # Report results
        self.report_results()

        return len(self.errors) == 0

    def validate_package_structure(self):
        """Validate package directory structure."""
        print("📁 Validating package structure...")

        required_files = [
            "pyproject.toml",
            "README.md",
            "LICENSE",
            "CHANGELOG.md",
            "MANIFEST.in",
            "src/spec_server/__init__.py",
            "src/spec_server/main.py",
            "src/spec_server/server.py",
            "src/spec_server/mcp_tools.py",
            "tests/conftest.py",
        ]

        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                self.errors.append(f"Missing required file: {file_path}")

        # Check for Python cache directories
        cache_dirs = list(self.project_root.rglob("__pycache__"))
        if cache_dirs:
            self.warnings.append(f"Found {len(cache_dirs)} __pycache__ directories")

    def validate_pyproject_toml(self):
        """Validate pyproject.toml configuration."""
        print("⚙️ Validating pyproject.toml...")

        pyproject_file = self.project_root / "pyproject.toml"
        if not pyproject_file.exists():
            self.errors.append("Missing pyproject.toml file")
            return

        try:
            import tomllib

            with open(pyproject_file, "rb") as f:
                config = tomllib.load(f)
        except ImportError:
            # Fallback for Python < 3.11
            try:
                import tomli

                with open(pyproject_file, "rb") as f:
                    config = tomli.load(f)
            except ImportError:
                self.warnings.append("Cannot validate pyproject.toml: tomllib/tomli not available")
                return
        except Exception as e:
            self.errors.append(f"Invalid pyproject.toml: {e}")
            return

        # Validate required sections
        required_sections = ["build-system", "project"]
        for section in required_sections:
            if section not in config:
                self.errors.append(f"Missing section in pyproject.toml: {section}")

        # Validate project metadata
        if "project" in config:
            project = config["project"]
            required_fields = ["name", "version", "description", "dependencies"]
            for field in required_fields:
                if field not in project:
                    self.errors.append(f"Missing project field in pyproject.toml: {field}")

            # Check version format
            if "version" in project:
                version = project["version"]
                if not version or not isinstance(version, str):
                    self.errors.append("Invalid version in pyproject.toml")

    def validate_source_code(self):
        """Validate source code quality."""
        print("🐍 Validating source code...")

        python_files = list(self.src_dir.rglob("*.py"))
        if not python_files:
            self.errors.append("No Python files found in source directory")
            return

        for py_file in python_files:
            self.validate_python_file(py_file)

    def validate_python_file(self, file_path: Path):
        """Validate a single Python file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse AST to check syntax
            ast.parse(content)

            # Check for basic code quality issues
            if "print(" in content and "main.py" not in str(file_path):
                self.warnings.append(f"Found print statement in {file_path.name}")

            if "TODO" in content:
                self.warnings.append(f"Found TODO comment in {file_path.name}")

        except SyntaxError as e:
            self.errors.append(f"Syntax error in {file_path.name}: {e}")
        except Exception as e:
            self.warnings.append(f"Could not validate {file_path.name}: {e}")

    def validate_tests(self):
        """Validate test suite."""
        print("🧪 Validating tests...")

        if not self.tests_dir.exists():
            self.errors.append("Tests directory not found")
            return

        test_files = list(self.tests_dir.rglob("test_*.py"))
        if len(test_files) < 5:
            self.warnings.append(f"Only {len(test_files)} test files found")

        # Check for conftest.py
        conftest_files = list(self.tests_dir.rglob("conftest.py"))
        if not conftest_files:
            self.warnings.append("No conftest.py found in tests")

    def validate_documentation(self):
        """Validate documentation files."""
        print("📚 Validating documentation...")

        readme_file = self.project_root / "README.md"
        if readme_file.exists():
            content = readme_file.read_text()
            if len(content) < 500:
                self.warnings.append("README.md seems too short")

            required_sections = ["Installation", "Usage", "Features"]
            for section in required_sections:
                if section.lower() not in content.lower():
                    self.warnings.append(f"README.md missing section: {section}")

        # Check for documentation directory
        docs_dir = self.project_root / "docs"
        if docs_dir.exists():
            doc_files = list(docs_dir.rglob("*.md"))
            if not doc_files:
                self.warnings.append("docs directory exists but contains no markdown files")

    def validate_scripts(self):
        """Validate scripts directory."""
        print("📜 Validating scripts...")

        scripts_dir = self.project_root / "scripts"
        if not scripts_dir.exists():
            self.warnings.append("No scripts directory found")
            return

        script_files = list(scripts_dir.glob("*.sh"))
        for script_file in script_files:
            # Check if script is executable
            if not script_file.stat().st_mode & 0o111:
                self.warnings.append(f"Script not executable: {script_file.name}")

    def validate_imports(self):
        """Validate that all imports work correctly."""
        print("📦 Validating imports...")

        try:
            # Test importing main modules
            sys.path.insert(0, str(self.src_dir.parent))

            import spec_server
            import spec_server.main
            import spec_server.mcp_tools
            import spec_server.server  # noqa: F401

            print("✅ All main imports successful")

        except ImportError as e:
            self.errors.append(f"Import error: {e}")
        except Exception as e:
            self.errors.append(f"Unexpected error during import: {e}")
        finally:
            if str(self.src_dir.parent) in sys.path:
                sys.path.remove(str(self.src_dir.parent))

    def validate_entry_points(self):
        """Validate entry points work correctly."""
        print("🚪 Validating entry points...")

        try:
            # Check if main function exists and is callable
            sys.path.insert(0, str(self.src_dir.parent))

            from spec_server.main import main

            if not callable(main):
                self.errors.append("Main entry point is not callable")

        except ImportError as e:
            self.errors.append(f"Cannot import main entry point: {e}")
        except Exception as e:
            self.errors.append(f"Error validating entry point: {e}")
        finally:
            if str(self.src_dir.parent) in sys.path:
                sys.path.remove(str(self.src_dir.parent))

    def report_results(self):
        """Report validation results."""
        print("\n" + "=" * 60)
        print("📊 VALIDATION RESULTS")
        print("=" * 60)

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All validations passed! Package is ready for distribution.")
        elif not self.errors:
            print(f"\n✅ No errors found. {len(self.warnings)} warnings to consider.")
        else:
            print(f"\n❌ {len(self.errors)} errors must be fixed before distribution.")

        print("=" * 60)


def main():
    """Main validation function."""
    project_root = Path(__file__).parent.parent
    validator = PackageValidator(project_root)

    success = validator.validate_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
