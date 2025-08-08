#!/usr/bin/env python3
"""
Release helper script for intake-gfs-ncar.

This script helps automate the release process by:
1. Checking that the working directory is clean
2. Updating the version in pyproject.toml
3. Creating a git tag
4. Providing instructions for the release process

Usage:
    python scripts/release.py --version 0.3.0
    python scripts/release.py --version 0.3.0 --dry-run
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a shell command and return the result.

    Args:
        cmd: Command to run as a list of strings
        check: Whether to raise an exception on non-zero exit code

    Returns:
        CompletedProcess: Result of the command
    """
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def check_git_status() -> bool:
    """
    Check if the git working directory is clean.

    Returns:
        bool: True if working directory is clean
    """
    result = run_command(["git", "status", "--porcelain"])
    if result.stdout.strip():
        print("Error: Working directory is not clean. Please commit or stash changes.")
        print("Uncommitted changes:")
        print(result.stdout)
        return False
    return True


def check_git_branch() -> bool:
    """
    Check if we're on the main branch.

    Returns:
        bool: True if on main branch
    """
    result = run_command(["git", "branch", "--show-current"])
    current_branch = result.stdout.strip()
    if current_branch != "main":
        print(f"Warning: You are on branch '{current_branch}', not 'main'.")
        response = input("Continue anyway? (y/N): ")
        return response.lower() == "y"
    return True


def get_current_version() -> Optional[str]:
    """
    Get the current version from pyproject.toml.

    Returns:
        str: Current version or None if not found
    """
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        return None

    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if match:
        return match.group(1)

    print("Error: Could not find version in pyproject.toml")
    return None


def update_version(new_version: str, dry_run: bool = False) -> bool:
    """
    Update the version in pyproject.toml.

    Args:
        new_version: New version string
        dry_run: If True, don't actually update the file

    Returns:
        bool: True if successful
    """
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()

    # Find and replace version
    pattern = r'version = "[^"]+"'
    replacement = f'version = "{new_version}"'

    new_content = re.sub(pattern, replacement, content)
    if new_content == content:
        print("Error: Could not update version in pyproject.toml")
        return False

    if dry_run:
        print(f"Would update version to {new_version} in pyproject.toml")
    else:
        pyproject_path.write_text(new_content)
        print(f"Updated version to {new_version} in pyproject.toml")

    return True


def validate_version(version: str) -> bool:
    """
    Validate that the version string is in the correct format.

    Args:
        version: Version string to validate

    Returns:
        bool: True if version is valid
    """
    # Allow semantic versioning with optional pre-release identifiers
    # No leading zeros allowed in version numbers
    pattern = r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[a-zA-Z0-9]+(?:\.(?:0|[1-9]\d*))?)?$"
    if not re.match(pattern, version):
        print(
            f"Error: Invalid version format '{version}'. Expected format: X.Y.Z or X.Y.Z-prerelease"
        )
        return False
    return True


def create_git_tag(version: str, dry_run: bool = False) -> bool:
    """
    Create a git tag for the release.

    Args:
        version: Version to tag
        dry_run: If True, don't actually create the tag

    Returns:
        bool: True if successful
    """
    tag_name = f"v{version}"

    # Check if tag already exists
    result = run_command(["git", "tag", "-l", tag_name], check=False)
    if result.stdout.strip():
        print(f"Error: Tag {tag_name} already exists")
        return False

    if dry_run:
        print(f"Would create git tag: {tag_name}")
    else:
        # Commit the version change
        run_command(["git", "add", "pyproject.toml"])
        run_command(["git", "commit", "-m", f"Bump version to {version}"])

        # Create the tag
        run_command(["git", "tag", "-a", tag_name, "-m", f"Release {version}"])
        print(f"Created git tag: {tag_name}")

    return True


def print_release_instructions(version: str, dry_run: bool = False):
    """
    Print instructions for completing the release.

    Args:
        version: Version being released
        dry_run: Whether this was a dry run
    """
    tag_name = f"v{version}"

    if dry_run:
        print("\n" + "=" * 50)
        print("DRY RUN COMPLETE")
        print("=" * 50)
        print("This was a dry run. No changes were made.")
        print(f"To perform the actual release of version {version}:")
        print(f"python scripts/release.py --version {version}")
    else:
        print("\n" + "=" * 50)
        print("RELEASE PREPARATION COMPLETE")
        print("=" * 50)
        print(f"Version {version} has been prepared for release.")
        print("\nTo complete the release:")
        print("1. Push the changes and tag to GitHub:")
        print(f"   git push origin main")
        print(f"   git push origin {tag_name}")
        print("\n2. The GitHub Actions workflow will automatically:")
        print("   - Run tests")
        print("   - Build the package")
        print("   - Publish to PyPI")
        print("   - Create a GitHub release")
        print("\n3. Monitor the GitHub Actions workflow at:")
        print("   https://github.com/oceanum/intake-gfs-ncar/actions")


def main():
    """Main function to handle the release process."""
    parser = argparse.ArgumentParser(description="Release helper for intake-gfs-ncar")
    parser.add_argument(
        "--version", required=True, help="Version to release (e.g., 0.3.0)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    # Validate version format
    if not validate_version(args.version):
        sys.exit(1)

    # Get current version
    current_version = get_current_version()
    if not current_version:
        sys.exit(1)

    print(f"Current version: {current_version}")
    print(f"New version: {args.version}")

    if current_version == args.version:
        print("Error: New version is the same as current version")
        sys.exit(1)

    # Check git status
    if not check_git_status():
        sys.exit(1)

    # Check git branch
    if not check_git_branch():
        sys.exit(1)

    # Update version
    if not update_version(args.version, args.dry_run):
        sys.exit(1)

    # Create git tag
    if not create_git_tag(args.version, args.dry_run):
        sys.exit(1)

    # Print next steps
    print_release_instructions(args.version, args.dry_run)

    # Exit successfully
    sys.exit(0)


if __name__ == "__main__":
    main()
