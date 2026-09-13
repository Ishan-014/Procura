from dataclasses import dataclass


@dataclass
class AuthorityDecision:
    can_execute: bool
    requires_human: bool
    approver: str
    reason: str


def determine_authority(
    amount: float,
    requester_role: str,
    required_approver: str,
    approval_granted: bool = False,
) -> AuthorityDecision:

    if approval_granted:
        return AuthorityDecision(
            can_execute=True,
            requires_human=False,
            approver=required_approver,
            reason="Required approval has been granted.",
        )

    return AuthorityDecision(
        can_execute=False,
        requires_human=True,
        approver=required_approver,
        reason=(
            f"Purchase requires explicit approval "
            f"from {required_approver}."
        ),
    )