
import pytest

from services.workspace_manager import WorkspaceManager


@pytest.fixture
def manager(tmp_path):
    return WorkspaceManager(tmp_path / "workspace")


@pytest.fixture
def project(manager):
    return manager.create_workspace("Pharmacy Inventory Management")


def test_create_workspace(manager):
    project_dir = manager.create_workspace("Test Project")

    assert project_dir.exists()
    assert project_dir.is_dir()
    assert project_dir.is_relative_to(manager.workspace_root)


def test_write_and_read_file(manager, project):
    manager.write_file(project, "main.py", "print('Hello CodePilot')")

    content = manager.read_file(project, "main.py")

    assert content == "print('Hello CodePilot')"


def test_create_nested_file(manager, project):
    manager.write_file(project, "modules/inventory.py", "stock = []")

    assert manager.read_file(project, "modules/inventory.py") == "stock = []"


def test_reject_path_traversal(manager, project):
    with pytest.raises(ValueError, match="Path traversal"):
        manager.write_file(project, "../outside.py", "print('unsafe')")


def test_reject_absolute_path(manager, project):
    with pytest.raises(ValueError, match="Absolute file paths"):
        manager.write_file(project, str(manager.workspace_root / "outside.py"), "print('unsafe')")


def test_block_env_file(manager, project):
    with pytest.raises(ValueError, match="sensitive files"):
        manager.write_file(project, ".env", "SECRET=value")


def test_block_nested_env_file(manager, project):
    with pytest.raises(ValueError, match="sensitive files"):
        manager.write_file(project, "config/.env.production", "SECRET=value")


def test_reject_invalid_python_syntax(manager, project):
    with pytest.raises(ValueError, match="Python syntax error"):
        manager.write_file(project, "invalid.py", "def broken(")


def test_reject_empty_python_code(manager):
    with pytest.raises(ValueError, match="cannot be empty"):
        manager.validate_python_code("   ")


def test_reject_duplicate_file(manager, project):
    manager.write_file(project, "main.py", "print('first')")

    with pytest.raises(FileExistsError):
        manager.write_file(project, "main.py", "print('second')")


def test_allow_explicit_overwrite(manager, project):
    manager.write_file(project, "main.py", "print('first')")
    manager.write_file(
        project,
        "main.py",
        "print('second')",
        overwrite=True,
    )

    assert manager.read_file(project, "main.py") == "print('second')"


def test_list_files_excludes_sensitive_files(manager, project):
    manager.write_file(project, "main.py", "print('hello')")
    (project / ".env").write_text("SECRET=value", encoding="utf-8")

    files = manager.list_files(project)

    assert "main.py" in files
    assert ".env" not in files


def test_get_project_context(manager, project):
    manager.write_file(project, "main.py", "print('Pharmacy')")

    context = manager.get_project_context(project)

    assert "main.py" in context
    assert "print('Pharmacy')" in context


def test_reject_workspace_outside_root(manager, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()

    with pytest.raises(ValueError, match="outside the workspace root"):
        manager.list_files(outside)


def test_reject_workspace_root_itself(manager):
    with pytest.raises(ValueError, match="dedicated project workspace"):
        manager.list_files(manager.workspace_root)


def test_reject_oversized_file(manager, project):
    content = "x" * (manager.MAX_FILE_SIZE + 1)

    with pytest.raises(ValueError, match="1 MB size limit"):
        manager.write_file(project, "large.txt", content)
