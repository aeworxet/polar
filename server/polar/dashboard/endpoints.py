from typing import Any, Dict, List, Sequence, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import joinedload

from polar.auth.dependencies import Auth, UserRequiredAuth
from polar.authz.service import AccessType, Authz
from polar.dashboard.schemas import (
    Entry,
    IssueListResponse,
    IssueListType,
    IssueRelationship,
    IssueSortBy,
    IssueStatus,
    PaginationResponse,
    Relationship,
    RelationshipData,
)
from polar.enums import Platforms
from polar.exceptions import ResourceNotFound, Unauthorized
from polar.funding.schemas import PledgesTypeSummaries
from polar.issue.schemas import Issue as IssueSchema
from polar.issue.schemas import IssueReferenceRead
from polar.issue.service import issue
from polar.models.organization import Organization
from polar.models.repository import Repository
from polar.models.user import User
from polar.models.user_organization import UserOrganization
from polar.organization.schemas import Organization as OrganizationSchema
from polar.organization.service import organization as organization_service
from polar.pledge.schemas import Pledge as PledgeSchema
from polar.pledge.schemas import PledgeState
from polar.pledge.service import pledge as pledge_service
from polar.postgres import AsyncSession, get_db_session, sql
from polar.repository.schemas import Repository as RepositorySchema
from polar.repository.service import repository
from polar.reward.endpoints import to_resource
from polar.reward.schemas import Reward
from polar.reward.service import reward_service
from polar.user_organization.service import (
    user_organization as user_organization_service,
)

router = APIRouter(tags=["dashboard"])


@router.get(
    "/dashboard/personal",
    response_model=IssueListResponse,
)
async def get_personal_dashboard(
    auth: UserRequiredAuth,
    issue_list_type: IssueListType = IssueListType.issues,  # TODO: remove
    status: Union[List[IssueStatus], None] = Query(
        default=None
    ),  # TODO: remove, replace with show_closed
    q: Union[str, None] = Query(default=None),
    sort: Union[IssueSortBy, None] = Query(default=None),
    only_pledged: bool = Query(default=False),
    only_badged: bool = Query(default=False),
    page: int = Query(default=1),
    session: AsyncSession = Depends(get_db_session),
    authz: Authz = Depends(Authz.authz),
) -> IssueListResponse:
    return await dashboard(
        session=session,
        auth=auth,
        authz=authz,
        q=q,
        sort=sort,
        in_repos=[],
        page=page,
        for_user=auth.user,
        only_pledged=only_pledged,
        only_badged=only_badged,
        show_closed=status is not None and IssueStatus.closed in status,
    )


@router.get(
    "/dashboard/{platform}/{org_name}",
    response_model=IssueListResponse,
)
async def get_dashboard(
    platform: Platforms,
    org_name: str,
    repo_name: Union[str, None] = Query(default=None),
    issue_list_type: IssueListType = IssueListType.issues,  # TODO: remove
    status: Union[List[IssueStatus], None] = Query(
        default=None
    ),  # TODO: remove, replace with show_closed
    q: Union[str, None] = Query(default=None),
    sort: Union[IssueSortBy, None] = Query(default=None),
    only_pledged: bool = Query(default=False),
    only_badged: bool = Query(default=False),
    page: int = Query(default=1),
    auth: Auth = Depends(Auth.current_user),
    session: AsyncSession = Depends(get_db_session),
    authz: Authz = Depends(Authz.authz),
) -> IssueListResponse:
    if not auth.user:
        raise Unauthorized()

    org = await organization_service.get_by_name(session, platform, org_name)
    if not org:
        raise ResourceNotFound()

    # only if user is a member of this org
    if not await user_organization_service.get_by_user_and_org(
        session,
        auth.user.id,
        organization_id=org.id,
    ):
        raise Unauthorized()

    repositories: Sequence[Repository] = []

    # if repo name is set, use that repository
    if repo_name:
        repo = await repository.get_by_org_and_name(
            session,
            organization_id=org.id,
            name=repo_name,
            load_organization=True,
        )
        if not repo:
            raise HTTPException(
                status_code=404,
                detail="Repository not found",
            )
        repositories = [repo]
    else:
        repositories = await repository.list_by(
            session,
            org_ids=[org.id],
            load_organization=True,
        )

    # Limit to repositories that the authed subject can read
    repositories = [
        r for r in repositories if await authz.can(auth.subject, AccessType.read, r)
    ]

    if not repositories:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    return await dashboard(
        session=session,
        auth=auth,
        authz=authz,
        in_repos=repositories,
        q=q,
        sort=sort,
        for_org=org,
        only_pledged=only_pledged,
        only_badged=only_badged,
        show_closed=status is not None and IssueStatus.closed in status,
        page=page,
    )


def default_sort(
    issue_list_type: IssueListType,
    q: Union[str, None] = None,
) -> IssueSortBy:
    if q:
        return IssueSortBy.relevance

    if issue_list_type == IssueListType.issues:
        return IssueSortBy.issues_default

    if issue_list_type == IssueListType.dependencies:
        return IssueSortBy.dependencies_default

    return IssueSortBy.newest


async def dashboard(
    session: AsyncSession,
    auth: Auth,
    authz: Authz,
    in_repos: Sequence[Repository] = [],
    issue_list_type: IssueListType = IssueListType.issues,
    q: Union[str, None] = None,
    sort: Union[IssueSortBy, None] = None,
    for_org: Organization | None = None,
    for_user: User | None = None,
    only_pledged: bool = False,
    only_badged: bool = False,
    show_closed: bool = False,
    page: int = 1,
) -> IssueListResponse:
    # Default sorting
    if not sort:
        sort = default_sort(issue_list_type, q)

    # Pagination.
    # Page 1 is the first page
    limit = 100
    offset = (page - 1) * limit

    #
    # Select top level issues
    #
    (issues, total_issue_count) = await issue.list_by_repository_type_and_status(
        session,
        [r.id for r in in_repos],
        text=q,
        pledged_by_org=None,
        pledged_by_user=for_user.id
        if for_user and IssueListType.dependencies
        else None,
        have_pledge=True if only_pledged else None,
        have_polar_badge=True if only_badged else None,
        load_references=True,
        load_pledges=True,
        load_repository=True,
        show_closed=show_closed,
        show_closed_if_needs_action=True,
        sort_by=sort,
        limit=limit,
        offset=offset,
    )

    included: dict[str, Entry[Any]] = {}

    # start building issue relationships with pledges
    issue_relationships: Dict[UUID, IssueRelationship] = {}

    def issue_relationship(
        issue_id: UUID, key: str, default: RelationshipData | List[RelationshipData]
    ) -> Relationship:
        return issue_relationships.setdefault(issue_id, IssueRelationship()).setdefault(
            key, Relationship(data=default)
        )

    pledge_statuses = list(
        set(PledgeState.active_states()) | set([PledgeState.disputed])
    )

    # load user memberships
    user_memberships: Sequence[UserOrganization] = []
    if auth.user:
        user_memberships = await user_organization_service.list_by_user_id(
            session,
            auth.user.id,
        )

    # add pledges to included
    issue_pledges: dict[UUID, list[PledgeSchema]] = {}
    for i in issues:
        for pled in i.pledges:
            # Filter out invalid pledges
            if pled.state not in pledge_statuses:
                continue

            pledge_schema = PledgeSchema.from_db(pled)

            # Add user-specific metadata
            if auth.user:
                pledge_schema.authed_can_admin_sender = (
                    pledge_service.user_can_admin_sender_pledge(
                        auth.user, pled, user_memberships
                    )
                )
                pledge_schema.authed_can_admin_received = (
                    pledge_service.user_can_admin_received_pledge(
                        pled, user_memberships
                    )
                )

            included[str(pled.id)] = Entry(
                id=pled.id, type="pledge", attributes=pledge_schema
            )

            # inject relationships
            pledge_relationship = issue_relationship(pled.issue_id, "pledges", [])
            if isinstance(pledge_relationship.data, list):  # it always is
                pledge_relationship.data.append(
                    RelationshipData(type="pledge", id=pled.id)
                )

            irefs = issue_pledges.get(i.id, [])
            irefs.append(pledge_schema)
            issue_pledges[i.id] = irefs

    # get linked pull requests
    issue_references: dict[UUID, list[IssueReferenceRead]] = {}
    for i in issues:
        refs = i.references
        for ref in refs:
            included[ref.external_id] = Entry(
                id=ref.external_id,
                type="reference",
                attributes=IssueReferenceRead.from_model(ref),
            )

            ir = issue_relationship(ref.issue_id, "references", [])
            if isinstance(ir.data, list):  # it always is
                ir.data.append(RelationshipData(type="reference", id=ref.external_id))

            issue_refs = issue_references.get(ref.issue_id, [])
            issue_refs.append(IssueReferenceRead.from_model(ref))
            issue_references[ref.issue_id] = issue_refs

    # get pledge summary (public data, vs pledges who are dependent on who you are)
    pledge_summaries = await pledge_service.issues_pledge_type_summary(
        session,
        issues=issues,
    )
    issue_pledge_summaries: dict[UUID, PledgesTypeSummaries] = {}
    for issue_id, summary in pledge_summaries.items():
        key = f"ps_{issue_id}"
        included[key] = Entry(
            id=key,
            type="pledge_summary",
            attributes=summary,
        )

        # JSON:API
        issue_relationship(
            issue_id, "pledge_summary", RelationshipData(type="pledge_summary", id=key)
        )

        # Non JSON:API
        issue_pledge_summaries[issue_id] = summary

    # get rewards
    issue_rewards: dict[UUID, list[Reward]] = {}
    if for_org:
        rewards = await reward_service.list(session, issue_ids=[i.id for i in issues])
        for pledge, reward, transaction in rewards:
            reward_resource = to_resource(
                pledge,
                reward,
                transaction,
                include_admin_fields=await authz.can(
                    auth.subject, AccessType.write, pledge
                ),
            )

            key = f"reward_{pledge.id}_{reward.id}"
            included[key] = Entry(
                id=key,
                type="reward",
                attributes=reward_resource,
            )

            # JSON:API
            ir = issue_relationship(pledge.issue_id, "rewards", [])
            if isinstance(ir.data, list):  # it always is
                ir.data.append(RelationshipData(type="reward", id=key))

            # Non JSON:API
            ir2 = issue_rewards.get(pledge.issue_id, [])
            ir2.append(reward_resource)
            issue_rewards[pledge.issue_id] = ir2

    next_page = page + 1 if total_issue_count > page * limit else None

    data: List[Entry[IssueSchema]] = [
        Entry[IssueSchema](
            id=i.id,
            type="issue",
            attributes=IssueSchema.from_db(i),
            relationships=issue_relationships.get(i.id, None),
            rewards=issue_rewards.get(i.id, None),
            pledges_summary=issue_pledge_summaries.get(i.id, None),
            references=issue_references.get(i.id, None),
            pledges=issue_pledges.get(i.id, None),
        )
        for i in issues
    ]

    return IssueListResponse(
        data=data,  # type: ignore
        included=list(included.values()),
        pagination=PaginationResponse(
            total_count=total_issue_count,
            page=page,
            next_page=next_page,
        ),
    )


# An annoying hack to force the OpenAPI schema to include type definitions for
# PledgesTypeSummaries
@router.get(
    "/dashboard/dummy_do_not_use",
    response_model=PledgesTypeSummaries,
)
async def dummy_do_not_use() -> PledgesTypeSummaries:
    raise ResourceNotFound()
