
import pytest

from core.approval_manager import (
    ApprovalManager,
    ApprovalStatus,
)


def test_new_request_starts_pending():
    manager = ApprovalManager()

    request = manager.request_approval(
        action="Execute Python file",
        details="Run the generated pharmacy application.",
        resource="workspace/pharmacy_inventory/main.py",
    )

    assert request.status == ApprovalStatus.PENDING
    assert request.approval_id
    assert request.reviewed_at is None


def test_pending_request_can_be_approved():
    manager = ApprovalManager()

    request = manager.request_approval(
        "Execute code",
        "Run main.py",
        "workspace/main.py",
    )

    approved = manager.approve(request.approval_id)

    assert approved.status == ApprovalStatus.APPROVED
    assert approved.reviewed_at is not None
    assert manager.is_approved(request.approval_id) is True


def test_pending_request_can_be_rejected():
    manager = ApprovalManager()

    request = manager.request_approval(
        "Execute code",
        "Run main.py",
        "workspace/main.py",
    )

    rejected = manager.reject(request.approval_id)

    assert rejected.status == ApprovalStatus.REJECTED
    assert rejected.reviewed_at is not None
    assert manager.is_approved(request.approval_id) is False


def test_already_reviewed_request_cannot_be_approved_again():
    manager = ApprovalManager()

    request = manager.request_approval(
        "Execute code",
        "Run main.py",
        "workspace/main.py",
    )

    manager.approve(request.approval_id)

    with pytest.raises(ValueError):
        manager.approve(request.approval_id)


def test_rejected_request_cannot_be_approved():
    manager = ApprovalManager()

    request = manager.request_approval(
        "Execute code",
        "Run main.py",
        "workspace/main.py",
    )

    manager.reject(request.approval_id)

    with pytest.raises(ValueError):
        manager.approve(request.approval_id)


def test_unknown_approval_id_is_rejected():
    manager = ApprovalManager()

    with pytest.raises(KeyError):
        manager.get_request("unknown-id")


def test_empty_approval_details_are_rejected():
    manager = ApprovalManager()

    with pytest.raises(ValueError):
        manager.request_approval(
            "Execute code",
            "",
            "workspace/main.py",
        )


def test_list_requests_returns_all_requests():
    manager = ApprovalManager()

    manager.request_approval(
        "Execute code",
        "Run main.py",
        "workspace/main.py",
    )

    manager.request_approval(
        "Install dependency",
        "Install pytest",
        "workspace/requirements.txt",
    )

    assert len(manager.list_requests()) == 2
