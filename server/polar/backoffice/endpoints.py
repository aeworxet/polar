from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException

from polar.auth.dependencies import Auth
from polar.enums import Platforms
from polar.integrations.github.service.issue import github_issue
from polar.integrations.github.service.organization import (
    github_organization as github_organization_service,
)
from polar.integrations.github.service.repository import (
    github_repository as github_repository_service,
)
from polar.invite.schemas import InviteCreate, InviteRead
from polar.invite.service import invite as invite_service
from polar.models.organization import Organization
from polar.models.pledge_transaction import PledgeTransaction
from polar.organization.endpoints import OrganizationPrivateRead
from polar.organization.service import organization as organization_service
from polar.pledge.service import pledge as pledge_service
from polar.postgres import AsyncSession, get_db_session
from polar.reward.endpoints import to_resource as reward_to_resource
from polar.reward.schemas import Reward
from polar.reward.service import reward_service
from polar.types import ListResource

from .pledge_service import bo_pledges_service
from .schemas import (
    BackofficeBadge,
    BackofficeBadgeResponse,
    BackofficePledge,
    BackofficeReward,
)

router = APIRouter(tags=["backoffice"], prefix="/backoffice")

log = structlog.get_logger()


@router.get("/pledges", response_model=list[BackofficePledge])
async def pledges(
    auth: Auth = Depends(Auth.backoffice_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[BackofficePledge]:
    return await bo_pledges_service.list_pledges(session)


@router.get("/rewards", response_model=ListResource[BackofficeReward])
async def rewards(
    issue_id: UUID | None = None,
    auth: Auth = Depends(Auth.backoffice_user),
    session: AsyncSession = Depends(get_db_session),
) -> ListResource[BackofficeReward]:
    rewards = await reward_service.list(session, issue_id=issue_id)

    def r(r: Reward, trx: PledgeTransaction) -> BackofficeReward:
        return BackofficeReward(
            pledge=r.pledge,
            user=r.user,
            organization=r.organization,
            amount=r.amount,
            state=r.state,
            paid_at=r.paid_at,
            transfer_id=trx.transaction_id if trx else None,
        )

    return ListResource(
        items=[
            r(
                reward_to_resource(pledge, reward, transaction),
                transaction,
            )
            for pledge, reward, transaction in rewards
        ]
    )


async def get_pledge(session: AsyncSession, pledge_id: UUID) -> BackofficePledge:
    pledge = await pledge_service.get_with_loaded(session, pledge_id)
    if not pledge:
        raise HTTPException(
            status_code=404,
            detail="Pledge not found",
        )
    return BackofficePledge.from_db(pledge)


@router.post("/pledges/approve/{pledge_id}", response_model=BackofficePledge)
async def pledge_approve(
    pledge_id: UUID,
    auth: Auth = Depends(Auth.backoffice_user),
    session: AsyncSession = Depends(get_db_session),
) -> BackofficePledge:
    raise Exception("TODO")
    # await pledge_service.transfer(session, pledge_id)
    return await get_pledge(session, pledge_id)


@router.post("/pledges/mark_pending/{pledge_id}", response_model=BackofficePledge)
async def pledge_mark_pending(
    pledge_id: UUID,
    auth: Auth = Depends(Auth.backoffice_user),
    session: AsyncSession = Depends(get_db_session),
) -> BackofficePledge:
    await pledge_service.mark_pending_by_pledge_id(session, pledge_id)
    return await get_pledge(session, pledge_id)


@router.post("/pledges/mark_disputed/{pledge_id}", response_model=BackofficePledge)
async def pledge_mark_disputed(
    pledge_id: UUID,
    auth: Auth = Depends(Auth.backoffice_user),
    session: AsyncSession = Depends(get_db_session),
) -> BackofficePledge:
    await pledge_service.mark_disputed(
        session, pledge_id, by_user_id=auth.user.id, reason="Disputed via Backoffice"
    )
    return await get_pledge(session, pledge_id)


@router.post("/invites/create_code", response_model=InviteRead)
async def invites_create_code(
    invite: InviteCreate,
    auth: Auth = Depends(Auth.backoffice_user),
    session: AsyncSession = Depends(get_db_session),
) -> InviteRead:
    res = await invite_service.create_code(session, invite, auth.user)
    if not res:
        raise HTTPException(
            status_code=404,
            detail="Pledge not found",
        )
    return InviteRead.from_db(res)


@router.post("/invites/list", response_model=list[InviteRead])
async def invites_list(
    auth: Auth = Depends(Auth.backoffice_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[InviteRead]:
    res = await invite_service.list(session)
    return [InviteRead.from_db(i) for i in res]


@router.post("/organization/sync/{name}", response_model=OrganizationPrivateRead)
async def organization_sync(
    name: str,
    auth: Auth = Depends(Auth.backoffice_user),
    session: AsyncSession = Depends(get_db_session),
) -> Organization:
    org = await github_organization_service.get_by_name(session, Platforms.github, name)
    if not org:
        raise HTTPException(
            status_code=404,
            detail="Org not found",
        )

    await github_repository_service.install_for_organization(
        session, org, org.installation_id
    )

    return org


@router.post("/badge", response_model=BackofficeBadgeResponse)
async def manage_badge(
    badge: BackofficeBadge,
    auth: Auth = Depends(Auth.backoffice_user),
    session: AsyncSession = Depends(get_db_session),
) -> BackofficeBadgeResponse:
    log.info("backoffice.badge", badge=badge.dict(), admin=auth.user.username)

    org, repo, issue = await organization_service.get_with_repo_and_issue(
        session,
        platform=Platforms.github,
        org_name=badge.org_slug,
        repo_name=badge.repo_slug,
        issue=badge.issue_number,
    )

    if repo.pledge_badge_auto_embed:
        raise HTTPException(403)

    if badge.action == "remove":
        issue = await github_issue.remove_polar_label(
            session,
            organization=org,
            repository=repo,
            issue=issue,
        )
        success = not issue.has_pledge_badge_label
    else:
        issue = await github_issue.add_polar_label(
            session,
            organization=org,
            repository=repo,
            issue=issue,
        )
        success = issue.has_pledge_badge_label

    return BackofficeBadgeResponse(
        org_slug=org.name,
        repo_slug=repo.name,
        issue_number=issue.number,
        action=badge.action,
        success=success,
    )
