"""
SpecManager implementation for handling spec lifecycle management.

This module provides the SpecManager class which handles all file system operations
for specs, including directory creation, metadata tracking, and cleanup.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import get_effective_specs_dir
from .errors import ErrorCode, SpecError
from .models import Phase, Spec, SpecMetadata


class SpecManager:
    """
    Primary interface for spec lifecycle management.

    Handles all file system operations for specs, including directory creation,
    metadata tracking, and cleanup. Maintains a registry of all specs and their
    current states.
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the SpecManager.

        Args:
            base_path: Base directory for storing specs (None for auto-detection)
        """
        if base_path is None:
            self.base_path = get_effective_specs_dir()
        else:
            self.base_path = base_path
        self.metadata_file = self.base_path / ".spec-metadata.json"
        self._ensure_base_directory()

    def _ensure_base_directory(self) -> None:
        """Ensure the base specs directory exists."""
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _load_metadata_registry(self) -> Dict[str, Dict]:
        """Load the metadata registry from disk."""
        if not self.metadata_file.exists():
            return {}

        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                registry = json.load(f)
                return registry if isinstance(registry, dict) else {}
        except (json.JSONDecodeError, IOError):
            # If metadata file is corrupted, start fresh but log the issue
            return {}

    def _save_metadata_registry(self, registry: Dict[str, Dict]) -> None:
        """Save the metadata registry to disk."""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise SpecError(
                f"Failed to save metadata registry: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR,
                details={"file_path": str(self.metadata_file)},
            )

    def _get_spec_directory(self, feature_name: str) -> Path:
        """Get the directory path for a spec."""
        return self.base_path / feature_name

    def _determine_current_phase(self, spec_dir: Path) -> Phase:
        """Determine the current phase of a spec based on existing files."""
        requirements_exists = (spec_dir / "requirements.md").exists()
        design_exists = (spec_dir / "design.md").exists()
        tasks_exists = (spec_dir / "tasks.md").exists()

        if tasks_exists:
            return Phase.TASKS
        elif design_exists:
            return Phase.DESIGN
        elif requirements_exists:
            return Phase.REQUIREMENTS
        else:
            return Phase.REQUIREMENTS

    def _calculate_task_progress(self, spec_dir: Path) -> Optional[str]:
        """Calculate task progress from tasks.md file."""
        tasks_file = spec_dir / "tasks.md"
        if not tasks_file.exists():
            return None

        try:
            content = tasks_file.read_text(encoding="utf-8")

            # Count completed and total tasks
            completed_count = content.count("- [x]")
            total_count = content.count("- [")

            if total_count == 0:
                return None

            return f"{completed_count}/{total_count} completed"
        except IOError:
            return None

    def create_spec(self, feature_name: str, initial_idea: str) -> Spec:
        """
        Create a new specification.

        Args:
            feature_name: Kebab-case identifier for the feature
            initial_idea: User's rough feature description

        Returns:
            Created Spec instance

        Raises:
            SpecError: If spec already exists or creation fails
        """
        spec_dir = self._get_spec_directory(feature_name)

        # Check if spec already exists
        if spec_dir.exists():
            raise SpecError(
                f"Specification '{feature_name}' already exists",
                error_code=ErrorCode.SPEC_ALREADY_EXISTS,
                details={"feature_name": feature_name, "path": str(spec_dir)},
            )

        try:
            # Create spec directory
            spec_dir.mkdir(parents=True, exist_ok=False)

            # Create initial spec object
            now = datetime.now().isoformat()
            spec = Spec(
                feature_name=feature_name,
                current_phase=Phase.REQUIREMENTS,
                created_at=now,
                updated_at=now,
                base_path=spec_dir,
            )

            # Update metadata registry
            registry = self._load_metadata_registry()
            registry[feature_name] = {
                "created_at": spec.created_at,
                "updated_at": spec.updated_at,
                "current_phase": spec.current_phase,
                "initial_idea": initial_idea,
            }
            self._save_metadata_registry(registry)

            return spec

        except OSError as e:
            # Clean up on failure
            if spec_dir.exists():
                shutil.rmtree(spec_dir, ignore_errors=True)
            raise SpecError(
                f"Failed to create specification directory: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR,
                details={"feature_name": feature_name, "path": str(spec_dir)},
            )

    def get_spec(self, feature_name: str) -> Spec:
        """
        Get an existing specification.

        Args:
            feature_name: Kebab-case identifier for the feature

        Returns:
            Spec instance

        Raises:
            SpecError: If spec doesn't exist
        """
        spec_dir = self._get_spec_directory(feature_name)

        if not spec_dir.exists():
            raise SpecError(
                f"Specification '{feature_name}' not found",
                error_code=ErrorCode.SPEC_NOT_FOUND,
                details={"feature_name": feature_name, "path": str(spec_dir)},
            )

        # Load metadata from registry
        registry = self._load_metadata_registry()
        spec_metadata = registry.get(feature_name, {})

        # Determine current phase from filesystem
        current_phase = self._determine_current_phase(spec_dir)

        # Get timestamps from metadata or use file system times
        created_at = spec_metadata.get("created_at")
        updated_at = spec_metadata.get("updated_at")

        if not created_at:
            # Fallback to directory creation time
            stat = spec_dir.stat()
            created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()

        if not updated_at:
            # Fallback to directory modification time
            stat = spec_dir.stat()
            updated_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

        return Spec(
            feature_name=feature_name,
            current_phase=current_phase,
            created_at=created_at,
            updated_at=updated_at,
            base_path=spec_dir,
        )

    def list_specs(self) -> List[SpecMetadata]:
        """
        List all existing specifications with metadata.

        Returns:
            List of SpecMetadata instances
        """
        specs: List[SpecMetadata] = []

        # Scan directory for spec folders
        if not self.base_path.exists():
            return specs

        registry = self._load_metadata_registry()

        for item in self.base_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                feature_name = item.name

                # Get metadata from registry
                spec_metadata = registry.get(feature_name, {})

                # Check which files exist
                has_requirements = (item / "requirements.md").exists()
                has_design = (item / "design.md").exists()
                has_tasks = (item / "tasks.md").exists()

                # Determine current phase
                current_phase = self._determine_current_phase(item)

                # Calculate task progress
                task_progress = self._calculate_task_progress(item)

                # Get timestamps
                created_at = spec_metadata.get("created_at")
                updated_at = spec_metadata.get("updated_at")

                if not created_at:
                    stat = item.stat()
                    created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()

                if not updated_at:
                    stat = item.stat()
                    updated_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

                metadata = SpecMetadata(
                    feature_name=feature_name,
                    current_phase=current_phase,
                    has_requirements=has_requirements,
                    has_design=has_design,
                    has_tasks=has_tasks,
                    task_progress=task_progress,
                    created_at=created_at,
                    updated_at=updated_at,
                )

                specs.append(metadata)

        # Sort by creation time (newest first)
        specs.sort(key=lambda x: x.created_at, reverse=True)
        return specs

    def delete_spec(self, feature_name: str) -> bool:
        """
        Delete a specification entirely.

        Args:
            feature_name: Kebab-case identifier for the feature

        Returns:
            True if deletion was successful

        Raises:
            SpecError: If spec doesn't exist or deletion fails
        """
        spec_dir = self._get_spec_directory(feature_name)

        if not spec_dir.exists():
            raise SpecError(
                f"Specification '{feature_name}' not found",
                error_code=ErrorCode.SPEC_NOT_FOUND,
                details={"feature_name": feature_name, "path": str(spec_dir)},
            )

        try:
            # Remove spec directory and all contents
            shutil.rmtree(spec_dir)

            # Remove from metadata registry
            registry = self._load_metadata_registry()
            if feature_name in registry:
                del registry[feature_name]
                self._save_metadata_registry(registry)

            return True

        except OSError as e:
            raise SpecError(
                f"Failed to delete specification: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR,
                details={"feature_name": feature_name, "path": str(spec_dir)},
            )

    def update_spec_metadata(self, feature_name: str, **updates: Any) -> None:
        """
        Update metadata for a specification.

        Args:
            feature_name: Kebab-case identifier for the feature
            **updates: Metadata fields to update
        """
        spec_dir = self._get_spec_directory(feature_name)

        if not spec_dir.exists():
            raise SpecError(
                f"Specification '{feature_name}' not found",
                error_code=ErrorCode.SPEC_NOT_FOUND,
                details={"feature_name": feature_name},
            )

        registry = self._load_metadata_registry()

        if feature_name not in registry:
            registry[feature_name] = {}

        # Update metadata
        registry[feature_name].update(updates)
        registry[feature_name]["updated_at"] = datetime.now().isoformat()

        self._save_metadata_registry(registry)

    def spec_exists(self, feature_name: str) -> bool:
        """
        Check if a specification exists.

        Args:
            feature_name: Kebab-case identifier for the feature

        Returns:
            True if spec exists, False otherwise
        """
        spec_dir = self._get_spec_directory(feature_name)
        return spec_dir.exists()

    def get_spec_files_status(self, feature_name: str) -> Dict[str, bool]:
        """
        Get the status of spec files (which ones exist).

        Args:
            feature_name: Kebab-case identifier for the feature

        Returns:
            Dictionary with file existence status
        """
        spec_dir = self._get_spec_directory(feature_name)

        return {
            "requirements": (spec_dir / "requirements.md").exists(),
            "design": (spec_dir / "design.md").exists(),
            "tasks": (spec_dir / "tasks.md").exists(),
        }
