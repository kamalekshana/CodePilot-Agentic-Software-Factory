
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ApprovalRequest:
    approval_id: str
    action: str
    details: str
    resource: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    reviewed_at: datetime | None = None


class ApprovalManager:
    """Manages explicit human approval for sensitive operations."""

    def __init__(self):
        self._requests: dict[str, ApprovalRequest] = {}

    def request_approval(
        self,
        action: str,
        details: str,
        resource: str,
    ) -> ApprovalRequest:
        """Create a new pending approval request."""

        for value, label in (
            (action, "Action"),
            (details, "Details"),
            (resource, "Resource"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} cannot be empty.")

        request = ApprovalRequest(
            approval_id=str(uuid4()),
            action=action.strip(),
            details=details.strip(),
            resource=resource.strip(),
        )

        self._requests[request.approval_id] = request
        return request

    def get_request(self, approval_id: str) -> ApprovalRequest:
        """Retrieve an approval request by its ID."""

        if not isinstance(approval_id, str) or not approval_id.strip():
            raise ValueError("Approval ID cannot be empty.")

        request = self._requests.get(approval_id)

        if request is None:
            raise KeyError("Approval request was not found.")

        return request

    def approve(self, approval_id: str) -> ApprovalRequest:
        """Approve a pending request."""

        request = self.get_request(approval_id)

        if request.status != ApprovalStatus.PENDING:
            raise ValueError("Only pending requests can be approved.")

        request.status = ApprovalStatus.APPROVED
        request.reviewed_at = datetime.now(timezone.utc)
        return request

    def reject(self, approval_id: str) -> ApprovalRequest:
        """Reject a pending request."""

        request = self.get_request(approval_id)

        if request.status != ApprovalStatus.PENDING:
            raise ValueError("Only pending requests can be rejected.")

        request.status = ApprovalStatus.REJECTED
        request.reviewed_at = datetime.now(timezone.utc)
        return request

    def is_approved(self, approval_id: str) -> bool:
        """Check whether a request has been approved."""

        return (
            self.get_request(approval_id).status
            == ApprovalStatus.APPROVED
        )

    def list_requests(self) -> list[ApprovalRequest]:
        """Return all approval requests."""

        return list(self._requests.values())
