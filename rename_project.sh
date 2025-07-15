#!/bin/bash

# This script renames the project and its internal Python package.
# Usage: ./rename_project.sh <new-project-kebab-case> <new_package_snake_case> "New Project Title Case"

OLD_PROJECT_KEBAB="clean-python-template"
OLD_PACKAGE_SNAKE="clean_python_template"
OLD_PROJECT_TITLE="Clean Python Template"

NEW_PROJECT_KEBAB=$1
NEW_PACKAGE_SNAKE=$2
NEW_PROJECT_TITLE=$3

if [ -z "$NEW_PROJECT_KEBAB" ] || [ -z "$NEW_PACKAGE_SNAKE" ] || [ -z "$NEW_PROJECT_TITLE" ]; then
    echo "Usage: ./rename_project.sh <new-project-kebab-case> <new_package_snake_case> \"New Project Title Case\""
    exit 1
fi

echo "Renaming project from '$OLD_PROJECT_TITLE' to '$NEW_PROJECT_TITLE'"

# 1. Rename the main Python package directory
echo "- Renaming src/$OLD_PACKAGE_SNAKE to src/$NEW_PACKAGE_SNAKE"
mv "src/$OLD_PACKAGE_SNAKE" "src/$NEW_PACKAGE_SNAKE"

# 2. Update references in pyproject.toml
echo "- Updating pyproject.toml"
sed -i '' "s/name = \"$OLD_PROJECT_KEBAB\"/name = \"$NEW_PROJECT_KEBAB\"/g" pyproject.toml
sed -i '' "s/packages = \[{include = \"$OLD_PACKAGE_SNAKE\", from = \"src\"}\]/packages = \[{include = \"$NEW_PACKAGE_SNAKE\", from = \"src\"}\]/g" pyproject.toml
sed -i '' "s/cpt-cli = \"$OLD_PACKAGE_SNAKE.cli.main:app\"/${NEW_PROJECT_KEBAB}-cli = \"${NEW_PACKAGE_SNAKE}.cli.main:app\"/g" pyproject.toml
sed -i '' "s/cpt-server = \"$OLD_PACKAGE_SNAKE.server.main:app\"/${NEW_PROJECT_KEBAB}-server = \"${NEW_PACKAGE_SNAKE}.server.main:app\"/g" pyproject.toml

# 3. Update references in mkdocs.yml
echo "- Updating mkdocs.yml"
sed -i '' "s/site_name: $OLD_PROJECT_TITLE/site_name: $NEW_PROJECT_TITLE/g" mkdocs.yml

# 4. Update references in README.md
echo "- Updating README.md"
sed -i '' "s/# $OLD_PROJECT_TITLE/# $NEW_PROJECT_TITLE/g" README.md

# 5. Update references in src/<new_package_name>/server/main.py
echo "- Updating src/$NEW_PACKAGE_SNAKE/server/main.py"
sed -i '' "s/mcp = FastMCP(\"$OLD_PROJECT_TITLE\")/mcp = FastMCP(\"$NEW_PROJECT_TITLE\")/g" "src/$NEW_PACKAGE_SNAKE/server/main.py"

# 6. Global find/replace for package name in Python files
echo "- Updating import statements in Python files"
find "src/$NEW_PACKAGE_SNAKE" "tests" -type f -name "*.py" -exec sed -i '' "s/$OLD_PACKAGE_SNAKE/$NEW_PACKAGE_SNAKE/g" {} +

echo "\nRenaming complete!"
echo "\nNext steps:"
echo "1. Consider renaming the root project directory (if you haven't already)."
echo "2. Re-install dependencies to ensure everything is correctly linked:"
echo "   rm -rf .venv"
echo "   uv venv"
echo "   source .venv/bin/activate"
echo "   uv pip install -e .[dev]"
echo "3. Run tests to verify the changes:"
echo "   uv run pytest"
echo "4. Review the changes using 'git diff' and commit them."
