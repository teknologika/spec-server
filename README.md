# Clean Python Template

A template for creating robust Python projects.

## Features

-   Core library, CLI, and Server components
-   Testing with `pytest`
-   Linting with `flake8`
-   CI/CD with GitHub Actions
-   Documentation with MkDocs

## How to Use This Template (Renaming for Your Project)

When you create a new repository from this template, you'll want to rename it to reflect your new project's name. Let's assume your new project name is `MyAwesomeProject` and its corresponding Python package name is `my_awesome_project` (lowercase, snake_case).

Here's a step-by-step guide:

1.  **Rename the Root Project Directory (Optional, but Recommended):**
    After cloning the template, rename the top-level directory:
    ```bash
    mv CleanPythonTemplate MyAwesomeProject
    cd MyAwesomeProject
    ```

2.  **Rename the Main Python Package Directory:**
    This is crucial for imports and packaging.
    ```bash
    mv src/clean_python_template src/my_awesome_project
    ```

3.  **Update References in `pyproject.toml`:**
    Open `pyproject.toml` and update the following lines:
    *   `name = "clean-python-template"` to `name = "my-awesome-project"` (use kebab-case for the project name here).
    *   `packages = [{include = "clean_python_template", from = "src"}]` to `packages = [{include = "my_awesome_project", from = "src"}]`.
    *   Update the `cpt-cli` and `cpt-server` scripts to use your new package name (e.g., `my-awesome-cli`, `my-awesome-server`):
        ```toml
        [project.scripts]
        my-awesome-cli = "my_awesome_project.cli.main:app"
        my-awesome-server = "my_awesome_project.server.main:app"
        ```

4.  **Update References in `mkdocs.yml`:**
    Open `mkdocs.yml` and change:
    *   `site_name: Clean Python Template` to `site_name: My Awesome Project`.

5.  **Update References in `README.md` (This File!):**
    *   Update the main heading and any other mentions of "Clean Python Template" to "My Awesome Project".

6.  **Update References in `src/my_awesome_project/server/main.py`:**
    Open `src/my_awesome_project/server/main.py` and change:
    *   `mcp = FastMCP("CleanPythonTemplate")` to `mcp = FastMCP("MyAwesomeProject")`.

7.  **Update Import Statements (Global Find/Replace):**
    This is the most critical step. You'll need to replace all occurrences of the old package name in import statements.
    *   **Find:** `clean_python_template`
    *   **Replace With:** `my_awesome_project`
    *   You'll need to do this in:
        *   `src/my_awesome_project/cli/main.py`
        *   `src/my_awesome_project/server/main.py`
        *   `src/my_awesome_project/core/math.py` (if it imports anything from the main package)
        *   `tests/test_cli/test_main.py`
        *   `tests/test_server/test_main.py`

    *   **Example using `sed` (Linux/macOS - use with caution and back up first!):**
        ```bash
        # Navigate to your project root first
        # For .py files
        find . -type f -name "*.py" -exec sed -i '' 's/clean_python_template/my_awesome_project/g' {} +
        # For .toml files
        find . -type f -name "*.toml" -exec sed -i '' 's/clean-python-template/my-awesome-project/g' {} +
        # For .md files (adjust as needed for specific content)
        find . -type f -name "*.md" -exec sed -i '' 's/Clean Python Template/My Awesome Project/g' {} +
        ```
        *(Note: `sed -i ''` is for macOS. For Linux, it's `sed -i`)*

8.  **Re-install Dependencies:**
    After all these changes, it's a good idea to remove your old virtual environment and create a new one to ensure all paths are correctly resolved.
    ```bash
    rm -rf .venv
    uv venv
    source .venv/bin/activate
    uv pip install -e .[dev]
    ```

9.  **Run Tests to Verify:**
    Finally, run your tests to ensure everything is working as expected:
    ```bash
    uv run pytest
    ```

## Automated Renaming Script

To streamline the renaming process, an automated script `rename_project.sh` is provided in the project root. This script will perform most of the steps outlined above.

**Usage:**

1.  **Navigate to your project root:**
    ```bash
    cd /path/to/your/project
    ```
2.  **Run the script with your desired names:**
    ```bash
    ./rename_project.sh <new-project-kebab-case> <new_package_snake_case> "New Project Title Case"
    ```
    *   Replace `<new-project-kebab-case>` with your new project name in kebab-case (e.g., `my-awesome-project`).
    *   Replace `<new_package_snake_case>` with your new Python package name in snake_case (e.g., `my_awesome_project`).
    *   Replace `"New Project Title Case"` with your new project title in quotes (e.g., `"My Awesome Project"`).

After the script completes, follow the on-screen instructions to re-install dependencies, run tests, and commit your changes.

## Releases

This project uses GitHub Releases to automate the publishing of packages to PyPI and TestPyPI.

The `publish.yml` GitHub Actions workflow is configured to run only when a new GitHub Release is created. This ensures that publishing is a deliberate action tied to your release process.

**How to Create a Release:**

1.  **Through the GitHub Web Interface (Recommended):**
    *   Go to your repository on GitHub.
    *   Click on "Releases" (usually found on the right sidebar or under the "Code" tab).
    *   Click the "Draft a new release" button.
    *   Choose an existing Git tag or create a new one (e.g., `v1.0.0`). Creating a new tag here will automatically push it to your repository.
    *   Provide a release title and description.
    *   You can also attach binaries or other files if needed.
    *   Click "Publish release".

2.  **Using the GitHub CLI or API:**
    *   Create a Git tag locally: `git tag -a v1.0.0 -m "Release v1.0.0"`
    *   Push the tag to GitHub: `git push origin v1.0.0`
    *   Then, use the GitHub CLI (`gh release create v1.0.0 --title "Release v1.0.0" --notes "Release notes here"`) or the GitHub API to create the release associated with that tag.

Once a release is "created" (either via the UI or API), the `publish.yml` GitHub Actions workflow will automatically trigger and proceed with building and publishing your package.

## Pre-Commit Hooks

This project uses `pre-commit` to ensure code quality and consistency before commits are made. This helps catch issues early in the development cycle.

**Setup:**

1.  **Install `pre-commit`:**
    If you don't have `pre-commit` installed globally, you can install it using `uv`:
    ```bash
    uv pip install pre-commit
    ```

2.  **Install the Git hooks:**
    Navigate to your project root and run:
    ```bash
    pre-commit install
    ```

Once installed, `pre-commit` will automatically run the configured checks (e.g., linting, formatting, type checking) on your staged files before each commit. If any checks fail, the commit will be aborted, allowing you to fix the issues.
