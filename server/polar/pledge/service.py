from __future__ import annotations

import datetime
from datetime import timedelta
from typing import Any, Awaitable, Callable, List, Sequence
from uuid import UUID

import structlog
from discord_webhook import AsyncDiscordWebhook, DiscordEmbed
from sqlalchemy.orm import (
    joinedload,
)

from polar.account.service import account as account_service
from polar.config import settings
from polar.currency.schemas import CurrencyAmount
from polar.exceptions import (
    InternalServerError,
    NotPermitted,
    ResourceNotFound,
)
from polar.funding.funding_schema import Funding
from polar.funding.schemas import PledgesSummary as FundingPledgesSummary
from polar.funding.schemas import PledgesTypeSummaries
from polar.integrations.github.service.user import github_user as github_user_service
from polar.integrations.loops.service import loops as loops_service
from polar.integrations.stripe.schemas import PaymentIntentSuccessWebhook
from polar.integrations.stripe.service import stripe as stripe_service
from polar.issue.schemas import ConfirmIssueSplit
from polar.issue.service import issue as issue_service
from polar.kit.hook import Hook
from polar.kit.services import ResourceServiceReader
from polar.kit.utils import utc_now
from polar.models.account import Account
from polar.models.issue import Issue
from polar.models.issue_reward import IssueReward
from polar.models.pledge import Pledge
from polar.models.pledge_transaction import PledgeTransaction
from polar.models.repository import Repository
from polar.models.user import User
from polar.models.user_organization import UserOrganization
from polar.notifications.notification import (
    MaintainerPledgedIssueConfirmationPendingNotification,
    MaintainerPledgedIssuePendingNotification,
    PledgerPledgePendingNotification,
    RewardPaidNotification,
)
from polar.notifications.service import (
    PartialNotification,
    get_cents_in_dollar_string,
)
from polar.notifications.service import (
    notifications as notification_service,
)
from polar.organization.service import organization as organization_service
from polar.postgres import AsyncSession, sql
from polar.repository.service import repository as repository_service
from polar.user.service import user as user_service

from .hooks import (
    PledgeHook,
    pledge_created,
    pledge_disputed,
    pledge_updated,
)
from .schemas import (
    PledgePledgesSummary,
    Pledger,
    PledgeState,
    PledgeTransactionType,
    PledgeType,
    SummaryPledge,
)

log = structlog.get_logger()


class PledgeService(ResourceServiceReader[Pledge]):
    async def get_with_loaded(
        self,
        session: AsyncSession,
        pledge_id: UUID,
    ) -> Pledge | None:
        statement = (
            sql.select(Pledge)
            .options(
                joinedload(Pledge.user),
                joinedload(Pledge.by_organization),
                joinedload(Pledge.on_behalf_of_organization),
                joinedload(Pledge.issue).joinedload(Issue.organization),
                joinedload(Pledge.issue)
                .joinedload(Issue.repository)
                .joinedload(Repository.organization),
            )
            .filter(Pledge.id == pledge_id)
        )
        res = await session.execute(statement)
        return res.scalars().unique().one_or_none()

    async def list_by(
        self,
        session: AsyncSession,
        organization_ids: list[UUID] | None = None,
        repository_ids: list[UUID] | None = None,
        issue_ids: list[UUID] | None = None,
        pledging_user: UUID | None = None,
        load_issue: bool = False,
        load_pledger: bool = False,
        all_states: bool = False,
    ) -> Sequence[Pledge]:
        statement = sql.select(Pledge)

        if not all_states:
            statement = statement.where(
                Pledge.state.in_(PledgeState.active_states()),
            )

        if organization_ids:
            statement = statement.where(Pledge.organization_id.in_(organization_ids))

        if repository_ids:
            statement = statement.where(Pledge.repository_id.in_(repository_ids))

        if pledging_user:
            statement = statement.where(Pledge.by_user_id == pledging_user)

        if issue_ids:
            statement = statement.where(Pledge.issue_id.in_(issue_ids))

        if load_issue:
            statement = statement.options(
                joinedload(Pledge.issue).joinedload(Issue.organization),
                joinedload(Pledge.issue)
                .joinedload(Issue.repository)
                .joinedload(Repository.organization),
            )

        if load_pledger:
            statement = statement.options(
                joinedload(Pledge.by_organization),
                joinedload(Pledge.user),
                joinedload(Pledge.on_behalf_of_organization),
            )

        statement = statement.order_by(Pledge.created_at)

        res = await session.execute(statement)
        return res.scalars().unique().all()

    async def list_by_repository(
        self, session: AsyncSession, repository_id: UUID
    ) -> Sequence[Pledge]:
        # Deprecated, please use list_by directly
        return await self.list_by(session, repository_ids=[repository_id])

    async def list_by_pledging_user(
        self, session: AsyncSession, user_id: UUID
    ) -> Sequence[Pledge]:
        # Deprecated, please use list_by directly
        return await self.list_by(session, pledging_user=user_id)

    async def list_by_receiving_organization(
        self, session: AsyncSession, organization_id: UUID
    ) -> Sequence[Pledge]:
        statement = (
            sql.select(Pledge)
            .where(
                Pledge.organization_id == organization_id,
                Pledge.state != PledgeState.initiated,
            )
            .options(
                joinedload(Pledge.user),
                joinedload(Pledge.by_organization),
                joinedload(Pledge.issue)
                .joinedload(Issue.repository)
                .joinedload(Repository.organization),
                joinedload(Pledge.to_repository).joinedload(Repository.organization),
                joinedload(Pledge.to_organization),
                joinedload(Pledge.on_behalf_of_organization),
            )
        )
        res = await session.execute(statement)
        return res.scalars().unique().all()

    async def get_by_issue_ids(
        self,
        session: AsyncSession,
        issue_ids: List[UUID],
    ) -> Sequence[Pledge]:
        if not issue_ids:
            return []
        statement = (
            sql.select(Pledge)
            .options(
                joinedload(Pledge.user),
                joinedload(Pledge.by_organization),
                joinedload(Pledge.on_behalf_of_organization),
            )
            .filter(
                Pledge.issue_id.in_(issue_ids),
                Pledge.state.in_(PledgeState.active_states()),
            )
        )
        res = await session.execute(statement)
        return res.scalars().unique().all()

    async def connect_backer(
        self,
        session: AsyncSession,
        payment_intent_id: str,
        backer: User,
    ) -> None:
        pledge = await self.get_by_payment_id(session, payment_id=payment_intent_id)
        if not pledge:
            raise ResourceNotFound(
                f"Pledge not found with payment_id: {payment_intent_id}"
            )

        # This pledge is already connected
        if pledge.by_user_id or pledge.by_organization_id:
            return None

        pledge.by_user_id = backer.id
        await pledge.save(session)

    async def transition_by_issue_id(
        self,
        session: AsyncSession,
        issue_id: UUID,
        from_states: list[PledgeState],
        to_state: PledgeState,
        hook: Hook[PledgeHook] | None = None,
        callback: Callable[[PledgeHook], Awaitable[None]] | None = None,
    ) -> bool:
        get = sql.select(Pledge).where(
            Pledge.issue_id == issue_id,
            Pledge.state.in_(from_states),
            Pledge.type == PledgeType.pay_upfront,
        )

        res = await session.execute(get)
        pledges = res.scalars().unique().all()

        values: dict[str, Any] = {
            "state": to_state,
        }

        if to_state == PledgeState.pending:
            values["scheduled_payout_at"] = utc_now() + timedelta(days=7)

        for pledge in pledges:
            # Update pledge
            statement = (
                sql.update(Pledge)
                .where(
                    Pledge.id == pledge.id,
                    Pledge.state.in_(from_states),
                )
                .values(values)
                .returning(Pledge)
            )
            await session.execute(statement)
            await session.commit()

            # FIXME: it would be cool if we could only trigger these events if the
            # update statement above modified the record
            await pledge_updated.call(PledgeHook(session, pledge))

            if hook:
                await hook.call(PledgeHook(session, pledge))

            if callback:
                await callback(PledgeHook(session, pledge))

        if len(pledges) > 0:
            return True
        return False

    async def pledge_confirmation_pending_notifications(
        self, session: AsyncSession, issue_id: UUID
    ) -> None:
        pledges = await self.list_by(session, issue_ids=[issue_id])

        # This issue doesn't have any pledges, don't send any notifications
        if len(pledges) == 0:
            return

        issue = await issue_service.get(session, issue_id)
        if not issue:
            raise Exception("issue not found")

        org = await organization_service.get(session, issue.organization_id)
        if not org:
            raise Exception("org not found")

        repo = await repository_service.get(session, issue.repository_id)
        if not repo:
            raise Exception("repo not found")

        org_account: Account | None = await account_service.get_by_org(session, org.id)

        pledge_amount_sum = sum([p.amount for p in pledges])

        n = MaintainerPledgedIssueConfirmationPendingNotification(
            pledge_amount_sum=get_cents_in_dollar_string(pledge_amount_sum),
            issue_url=f"https://github.com/{org.name}/{repo.name}/issues/{issue.number}",
            issue_title=issue.title,
            issue_org_name=org.name,
            issue_repo_name=repo.name,
            issue_number=issue.number,
            maintainer_has_account=True if org_account else False,
            issue_id=issue.id,
        )

        await notification_service.send_to_org(
            session=session,
            org_id=org.id,
            notif=PartialNotification(issue_id=issue.id, payload=n),
        )

    async def mark_pending_by_issue_id(
        self,
        session: AsyncSession,
        issue_id: UUID,
    ) -> None:
        async def send_pledger_notification(hook: PledgeHook) -> None:
            await self.send_pledger_pending_notification(hook.session, hook.pledge.id)

        # transition pay_upfront to pending
        # (invoiced pledges are moved to pending _after_ the invoice has been paid)
        #
        # sends notifications to pledgers for pledges that are transitioned
        # (via the callback)
        any_upfront_changed = await self.transition_by_issue_id(
            session,
            issue_id,
            from_states=PledgeState.to_pending_states(),
            to_state=PledgeState.pending,
            callback=send_pledger_notification,
        )

        # send invoices for pay later peldges thate still don't have one sent
        # sends notifications to pledgers that gets an invoice sent
        any_invoices_sent = await self.send_invoices(session, issue_id)

        # send notifications to maintainers
        if any_upfront_changed or any_invoices_sent:
            await self.send_maintainer_pending_notification(session, issue_id)

    async def issue_confirmed_discord_alert(self, issue: Issue) -> None:
        if not settings.DISCORD_WEBHOOK_URL:
            return

        webhook = AsyncDiscordWebhook(
            url=settings.DISCORD_WEBHOOK_URL, content="Confirmed issue"
        )

        embed = DiscordEmbed(
            title="Confirmed issue",
            description=f'"{issue.title}" has been confirmed solved',  # noqa: E501
            color="65280",
        )

        embed.add_embed_field(
            name="Backoffice",
            value=f"[Open](https://polar.sh/backoffice/issue/{str(issue.id)})",
        )

        webhook.add_embed(embed)
        await webhook.execute()

    async def send_maintainer_pending_notification(
        self, session: AsyncSession, issue_id: UUID
    ) -> None:
        pledges = await self.list_by(session, issue_ids=[issue_id])

        # This issue doesn't have any pledges, don't send any notifications
        if len(pledges) == 0:
            return

        issue = await issue_service.get(session, issue_id)
        if not issue:
            raise Exception("issue not found")

        org = await organization_service.get(session, issue.organization_id)
        if not org:
            raise Exception("org not found")

        repo = await repository_service.get(session, issue.repository_id)
        if not repo:
            raise Exception("repo not found")

        org_account: Account | None = await account_service.get_by_org(session, org.id)

        pledge_amount_sum = sum([p.amount for p in pledges])

        n = MaintainerPledgedIssuePendingNotification(
            pledge_amount_sum=get_cents_in_dollar_string(pledge_amount_sum),
            issue_url=f"https://github.com/{org.name}/{repo.name}/issues/{issue.number}",
            issue_title=issue.title,
            issue_org_name=org.name,
            issue_repo_name=repo.name,
            issue_number=issue.number,
            maintainer_has_account=True if org_account else False,
            issue_id=issue_id,
        )

        await notification_service.send_to_org(
            session=session,
            org_id=org.id,
            notif=PartialNotification(issue_id=issue_id, payload=n),
        )

    async def send_pledger_pending_notification(
        self,
        session: AsyncSession,
        pledge_id: UUID,
    ) -> None:
        pledge = await self.get(session, pledge_id)
        if not pledge:
            raise Exception("pledge not found")

        issue = await issue_service.get(session, pledge.issue_id)
        if not issue:
            raise Exception("issue not found")

        org = await organization_service.get(session, issue.organization_id)
        if not org:
            raise Exception("org not found")

        repo = await repository_service.get(session, issue.repository_id)
        if not repo:
            raise Exception("repo not found")

        pledger_notif = PledgerPledgePendingNotification(
            pledge_amount=get_cents_in_dollar_string(pledge.amount),
            pledge_date=pledge.created_at.strftime("%Y-%m-%d"),
            issue_url=f"https://github.com/{org.name}/{repo.name}/issues/{issue.number}",
            issue_title=issue.title,
            issue_org_name=org.name,
            issue_repo_name=repo.name,
            issue_number=issue.number,
            pledge_id=pledge.id,
            pledge_type=PledgeType.from_str(pledge.type),
        )

        await notification_service.send_to_pledger(
            session,
            pledge,
            notif=PartialNotification(
                issue_id=pledge.issue_id, pledge_id=pledge.id, payload=pledger_notif
            ),
        )

    def validate_splits(self, splits: list[ConfirmIssueSplit]) -> bool:
        sum = 0.0
        for s in splits:
            sum += s.share_thousands

            if s.github_username and s.organization_id:
                return False

            if not s.github_username and not s.organization_id:
                return False

        if sum != 1000:
            return False

        return True

    async def create_issue_rewards(
        self, session: AsyncSession, issue_id: UUID, splits: list[ConfirmIssueSplit]
    ) -> list[IssueReward]:
        if not self.validate_splits(splits):
            raise Exception("invalid split configuration")

        nested = await session.begin_nested()

        stmt = sql.select(IssueReward).where(IssueReward.issue_id == issue_id)
        res = await session.execute(stmt)
        existing = res.scalars().unique().all()

        if len(existing) > 0:
            await nested.commit()
            raise Exception(f"issue already has splits set: issue_id={issue_id}")

        created_splits: list[IssueReward] = []

        for split in splits:
            # Associate github usernames with a user if a user with this username exists
            user_id: UUID | None = None
            if split.github_username:
                user = await github_user_service.get_user_by_github_username(
                    session, split.github_username
                )
                if user:
                    user_id = user.id

            s = await IssueReward.create(
                session,
                autocommit=False,
                issue_id=issue_id,
                share_thousands=split.share_thousands,
                github_username=split.github_username,
                organization_id=split.organization_id,
                user_id=user_id,
            )
            created_splits.append(s)

        await nested.commit()
        await session.commit()

        return created_splits

    async def handle_payment_intent_success(
        self,
        session: AsyncSession,
        payload: PaymentIntentSuccessWebhook,
    ) -> None:
        pledge = await self.get_by_payment_id(session, payload.id)
        if not pledge:
            raise ResourceNotFound(f"Pledge not found with payment_id: {payload.id}")

        log.info(
            "handle_payment_intent_success",
            payment_id=payload.id,
        )

        # Log Transaction
        session.add(
            PledgeTransaction(
                pledge_id=pledge.id,
                type=PledgeTransactionType.pledge,
                amount=payload.amount_received,
                transaction_id=payload.latest_charge,
            )
        )
        await session.commit()

        if pledge.type == PledgeType.pay_upfront:
            return await self.mark_created_by_payment_id(
                session,
                payment_id=payload.id,
                amount_received=payload.amount_received,
                transaction_id=payload.latest_charge,
            )

        if pledge.type == PledgeType.pay_on_completion:
            return await self.handle_paid_invoice(
                session,
                payment_id=payload.id,
                amount_received=payload.amount_received,
                transaction_id=payload.latest_charge,
            )

        raise Exception(f"unhandeled pledge type type: {pledge.type}")

    async def mark_created_by_payment_id(
        self,
        session: AsyncSession,
        payment_id: str,
        amount_received: int,
        transaction_id: str,
    ) -> None:
        pledge = await self.get_by_payment_id(session, payment_id)
        if not pledge:
            raise ResourceNotFound(f"Pledge not found with payment_id: {payment_id}")

        # Already in the expected state
        if pledge.state == PledgeState.created:
            return None

        if pledge.state not in PledgeState.to_created_states():
            raise Exception(f"pledge is in unexpected state: {pledge.state}")

        if pledge.type != PledgeType.pay_upfront:
            raise Exception(f"pledge is of unexpected type: {pledge.type}")

        stmt = (
            sql.Update(Pledge)
            .where(
                Pledge.id == pledge.id,
                Pledge.state.in_(PledgeState.to_created_states()),
            )
            .values(
                state=PledgeState.created,
                amount_received=amount_received,
            )
        )
        await session.execute(stmt)
        await session.commit()
        await pledge_created.call(PledgeHook(session, pledge))

    async def handle_paid_invoice(
        self,
        session: AsyncSession,
        payment_id: str,
        amount_received: int,
        transaction_id: str,
    ) -> None:
        pledge = await self.get_by_payment_id(session, payment_id)
        if not pledge:
            raise ResourceNotFound(f"Pledge not found with payment_id: {payment_id}")

        if pledge.state not in PledgeState.to_pending_states():
            raise Exception(f"pledge is in unexpected state: {pledge.state}")

        if pledge.type != PledgeType.pay_on_completion:
            raise Exception(f"pledge is of unexpected type: {pledge.type}")

        stmt = (
            sql.Update(Pledge)
            .where(
                Pledge.id == pledge.id,
                Pledge.state.in_(PledgeState.to_pending_states()),
            )
            .values(
                state=PledgeState.pending,
                amount_received=amount_received,
            )
        )
        await session.execute(stmt)

        session.add(
            PledgeTransaction(
                pledge_id=pledge.id,
                type=PledgeTransactionType.pledge,
                amount=amount_received,
                transaction_id=transaction_id,
            )
        )
        await session.commit()
        await pledge_updated.call(PledgeHook(session, pledge))

    async def refund_by_payment_id(
        self, session: AsyncSession, payment_id: str, amount: int, transaction_id: str
    ) -> None:
        pledge = await self.get_by_payment_id(session, payment_id)
        if not pledge:
            raise ResourceNotFound(f"Pledge not found with payment_id: {payment_id}")

        if pledge.state not in PledgeState.to_refunded_states():
            raise NotPermitted("Refunding error, unexpected pledge status")

        pledge.refunded_at = utc_now()
        if amount == pledge.amount:
            pledge.state = PledgeState.refunded
        elif amount < pledge.amount:
            pledge.amount -= amount
        else:
            raise NotPermitted("Refunding error, unexpected amount!")
        session.add(pledge)
        session.add(
            PledgeTransaction(
                pledge_id=pledge.id,
                type=PledgeTransactionType.refund,
                amount=amount,
                transaction_id=transaction_id,
            )
        )
        await session.commit()
        await pledge_updated.call(PledgeHook(session, pledge))

    async def mark_charge_disputed_by_payment_id(
        self, session: AsyncSession, payment_id: str, amount: int, transaction_id: str
    ) -> None:
        pledge = await self.get_by_payment_id(session, payment_id)
        if not pledge:
            raise ResourceNotFound(f"Pledge not found with payment_id: {payment_id}")

        # charge_disputed (aka chargebacks) can be triggered from _any_ pledge state
        # not checking existing state here

        pledge.state = PledgeState.charge_disputed
        session.add(pledge)
        session.add(
            PledgeTransaction(
                pledge_id=pledge.id,
                type=PledgeTransactionType.disputed,
                amount=amount,
                transaction_id=transaction_id,
            )
        )
        await session.commit()
        await pledge_updated.call(PledgeHook(session, pledge))

    async def get_reward(
        self, session: AsyncSession, split_id: UUID
    ) -> IssueReward | None:
        stmt = sql.select(IssueReward).where(IssueReward.id == split_id)
        res = await session.execute(stmt)
        return res.scalars().unique().one_or_none()

    async def get_transaction(
        self,
        session: AsyncSession,
        type: PledgeTransactionType | None = None,
        pledge_id: UUID | None = None,
        issue_reward_id: UUID | None = None,
    ) -> PledgeTransaction | None:
        stmt = sql.select(PledgeTransaction)

        if type:
            stmt = stmt.where(PledgeTransaction.type == type)
        if pledge_id:
            stmt = stmt.where(PledgeTransaction.pledge_id == pledge_id)
        if issue_reward_id:
            stmt = stmt.where(PledgeTransaction.issue_reward_id == issue_reward_id)

        res = await session.execute(stmt)
        return res.scalars().unique().one_or_none()

    async def transfer(
        self, session: AsyncSession, pledge_id: UUID, issue_reward_id: UUID
    ) -> None:
        pledge = await self.get(session, id=pledge_id)
        if not pledge:
            raise ResourceNotFound(f"Pledge not found with id: {pledge_id}")
        if pledge.state not in PledgeState.to_paid_states():
            raise NotPermitted("Pledge is not in pending state")
        if pledge.scheduled_payout_at and pledge.scheduled_payout_at > utc_now():
            raise NotPermitted(
                "Pledge is not ready for payput (still in dispute window)"
            )

        # get receiver
        split = await self.get_reward(session, issue_reward_id)
        if not split:
            raise ResourceNotFound(f"IssueReward not found with id: {issue_reward_id}")

        # check that this split is for the same issue as the pledge
        if split.issue_id != pledge.issue_id:
            raise ResourceNotFound("IssueReward is not valid for this pledge_id")

        if not split.user_id and not split.organization_id:
            raise NotPermitted(
                "Either user_id or organization_id must be set on the split to create a transfer"  # noqa: E501
            )

        # sanity check
        if split.share_thousands < 0 or split.share_thousands > 1000:
            raise NotPermitted("unexpected split share")

        # check that this transfer hasn't already been made!
        existing_trx = await self.get_transaction(
            session, pledge_id=pledge.id, issue_reward_id=split.id
        )
        if existing_trx:
            raise NotPermitted(
                "A transfer for this pledge_id and issue_reward_id already exists, refusing to make another one"  # noqa: E501
            )

        # pledge amount - 10% (polars cut) * the users share
        payout_amount = round(pledge.amount * 0.9 * split.share_thousands / 1000)

        if split.user_id:
            pay_to_account = await account_service.get_by_user(session, split.user_id)
            if pay_to_account is None:
                raise NotPermitted("Receiving user has no account")

        elif split.organization_id:
            pay_to_account = await account_service.get_by_org(
                session, split.organization_id
            )
            if pay_to_account is None:
                raise NotPermitted("Receiving organization has no account")
        else:
            raise NotPermitted("Unexpected split receiver")

        transfer_id = account_service.transfer(
            session=session,
            account=pay_to_account,
            amount=payout_amount,
            transfer_group=f"{pledge.id}",
        )

        if transfer_id is None:
            raise NotPermitted("Transfer failed")  # TODO: Better error

        transaction = PledgeTransaction(
            pledge_id=pledge.id,
            type=PledgeTransactionType.transfer,
            amount=payout_amount,
            transaction_id=transfer_id,
            issue_reward_id=split.id,
        )

        session.add(transaction)
        await session.commit()

        # send notification
        await self.transfer_created_notification(session, pledge, transaction, split)

    async def transfer_created_notification(
        self,
        session: AsyncSession,
        pledge: Pledge,
        transaction: PledgeTransaction,
        split: IssueReward,
    ) -> None:
        issue = await issue_service.get(session, pledge.issue_id)
        if not issue:
            log.error("pledge_paid_notification.no_issue_found")
            return

        org = await organization_service.get(session, issue.organization_id)
        if not org:
            log.error("pledge_paid_notification.no_org_found")
            return

        repo = await repository_service.get(session, issue.repository_id)
        if not repo:
            log.error("pledge_paid_notification.no_repo_found")
            return

        n = RewardPaidNotification(
            issue_url=f"https://github.com/{org.name}/{repo.name}/issues/{issue.number}",
            issue_title=issue.title,
            issue_org_name=org.name,
            issue_repo_name=repo.name,
            issue_number=issue.number,
            paid_out_amount=get_cents_in_dollar_string(transaction.amount),
            pledge_id=pledge.id,
            issue_id=issue.id,
        )

        if split.organization_id:
            await notification_service.send_to_org(
                session=session,
                org_id=split.organization_id,
                notif=PartialNotification(
                    issue_id=pledge.issue_id, pledge_id=pledge.id, payload=n
                ),
            )
        elif split.user_id:
            await notification_service.send_to_user(
                session=session,
                user_id=split.user_id,
                notif=PartialNotification(
                    issue_id=pledge.issue_id, pledge_id=pledge.id, payload=n
                ),
            )

    async def get_by_payment_id(
        self, session: AsyncSession, payment_id: str
    ) -> Pledge | None:
        return await Pledge.find_by(
            session=session,
            payment_id=payment_id,
        )

    async def set_issue_pledged_amount_sum(
        self,
        session: AsyncSession,
        issue_id: UUID,
    ) -> None:
        pledges = await self.get_by_issue_ids(session, issue_ids=[issue_id])

        summed = sum(p.amount for p in pledges) if pledges else 0
        stmt = (
            sql.update(Issue)
            .where(Issue.id == issue_id)
            .values(pledged_amount_sum=summed)
        )

        await session.execute(stmt)
        await session.commit()

    async def mark_disputed(
        self,
        session: AsyncSession,
        pledge_id: UUID,
        by_user_id: UUID,
        reason: str,
    ) -> None:
        pledge = await self.get(session, id=pledge_id)
        if not pledge:
            raise ResourceNotFound(f"Pledge not found with id: {pledge_id}")
        if pledge.state not in PledgeState.to_disputed_states():
            raise NotPermitted(f"Pledge is unexpected state: {pledge.state}")

        stmt = (
            sql.update(Pledge)
            .where(Pledge.id == pledge_id)
            .values(
                state=PledgeState.disputed,
                dispute_reason=reason,
                disputed_at=datetime.datetime.now(),
                disputed_by_user_id=by_user_id,
            )
        )
        await session.execute(stmt)
        await session.commit()

        await pledge_disputed.call(PledgeHook(session, pledge))
        await pledge_updated.call(PledgeHook(session, pledge))

    async def create_pay_on_completion(
        self,
        session: AsyncSession,
        issue_id: UUID,
        by_user: User,
        amount: int,
        on_behalf_of_organization_id: UUID | None,
    ) -> Pledge:
        issue = await issue_service.get(session, issue_id)
        if not issue:
            raise ResourceNotFound("Issue Not Found")

        pledge = await Pledge.create(
            session=session,
            issue_id=issue.id,
            repository_id=issue.repository_id,
            organization_id=issue.organization_id,
            amount=amount,
            fee=0,
            state=PledgeState.created,
            type=PledgeType.pay_on_completion,
            by_user_id=by_user.id,
            on_behalf_of_organization_id=on_behalf_of_organization_id,
        )

        await loops_service.user_update(by_user, isBacker=True)

        await pledge_created.call(PledgeHook(session, pledge))

        return pledge

    async def send_invoices(
        self,
        session: AsyncSession,
        issue_id: UUID,
    ) -> bool:
        pledges = await self.list_by(session, issue_ids=[issue_id])
        any_sent = False
        for p in pledges:
            if p.type != PledgeType.pay_on_completion:
                continue
            if p.invoice_id:
                continue

            # send invoice via Stripe
            await self.send_invoice(session, p.id)
            any_sent = True

            # send notification to maintainer
            await self.send_pledger_pending_notification(session, p.id)

        return any_sent

    async def send_invoice(
        self,
        session: AsyncSession,
        pledge_id: UUID,
    ) -> None:
        pledge = await self.get(session, pledge_id)
        if not pledge:
            raise ResourceNotFound()

        if pledge.invoice_id:
            raise NotPermitted("this pledge already has an invoice")
        if pledge.type != PledgeType.pay_on_completion:
            raise NotPermitted("this pledge is not of type pay_on_completion")
        if not pledge.by_user_id:
            raise NotPermitted("this pledge is not made by a user")

        pledge_issue = await issue_service.get(session, pledge.issue_id)
        if not pledge_issue:
            raise ResourceNotFound()

        pledge_issue_repo = await repository_service.get(
            session, pledge_issue.repository_id
        )
        if not pledge_issue_repo:
            raise ResourceNotFound()

        pledge_issue_org = await organization_service.get(
            session, pledge_issue.organization_id
        )
        if not pledge_issue_org:
            raise ResourceNotFound()

        pledger_user = await user_service.get(session, pledge.by_user_id)
        if not pledger_user:
            raise ResourceNotFound()

        invoice = await stripe_service.create_pledge_invoice(
            session=session,
            user=pledger_user,
            pledge=pledge,
            pledge_issue=pledge_issue,
            pledge_issue_repo=pledge_issue_repo,
            pledge_issue_org=pledge_issue_org,
        )
        if not invoice:
            raise InternalServerError()

        stmt = (
            sql.Update(Pledge)
            .where(Pledge.id == pledge_id)
            .values(
                payment_id=invoice.payment_intent,
                invoice_id=invoice.id,
                invoice_hosted_url=invoice.hosted_invoice_url,
            )
        )
        await session.execute(stmt)
        await session.commit()
        return None

    def user_can_admin_sender_pledge(
        self, user: User, pledge: Pledge, memberships: Sequence[UserOrganization]
    ) -> bool:
        """
        Returns true if the User can modify the pledge on behalf of the entity that sent
        the pledge, such as disputing it.
        """

        if pledge.by_user_id == user.id:
            return True

        if pledge.by_organization_id:
            for m in memberships:
                if m.organization_id == pledge.by_organization_id and m.is_admin:
                    return True

        return False

    def user_can_admin_received_pledge(
        self, pledge: Pledge, memberships: Sequence[UserOrganization]
    ) -> bool:
        """
        Returns true if the User can modify the pledge on behalf of the entity that
        received the pledge, such as confirming it, and managing payouts.
        """
        return any(
            m.organization_id == pledge.organization_id and m.is_admin
            for m in memberships
        )

    def user_can_admin_received_pledge_on_issue(
        self, issue: Issue, memberships: Sequence[UserOrganization]
    ) -> bool:
        return any(
            m.organization_id == issue.organization_id and m.is_admin
            for m in memberships
        )

    async def issue_pledge_summary(
        self, session: AsyncSession, issue: Issue
    ) -> PledgePledgesSummary:
        return (await self.issues_pledge_summary(session, [issue]))[issue.id]

    async def issues_pledge_summary(
        self, session: AsyncSession, issues: Sequence[Issue]
    ) -> dict[UUID, PledgePledgesSummary]:
        all_pledges = await self.list_by(
            session,
            issue_ids=[i.id for i in issues],
            load_pledger=True,
        )

        res: dict[UUID, PledgePledgesSummary] = {}

        pledges_by_issue: dict[UUID, list[Pledge]] = {}
        for p in all_pledges:
            exist = pledges_by_issue.get(p.issue_id, [])
            exist.append(p)
            pledges_by_issue[p.issue_id] = exist

        for i in issues:
            pledges = pledges_by_issue.get(i.id, [])

            sum_pledges = sum([p.amount for p in pledges])

            funding = Funding(
                funding_goal=CurrencyAmount(currency="USD", amount=i.funding_goal)
                if i.funding_goal
                else None,
                pledges_sum=CurrencyAmount(currency="USD", amount=sum_pledges),
            )

            summary_pledges = [SummaryPledge.from_db(p) for p in pledges]

            res[i.id] = PledgePledgesSummary(funding=funding, pledges=summary_pledges)

        return res

    async def issues_pledge_type_summary(
        self, session: AsyncSession, issues: Sequence[Issue]
    ) -> dict[UUID, PledgesTypeSummaries]:
        all_pledges = await self.list_by(
            session, issue_ids=[i.id for i in issues], load_pledger=True
        )

        res: dict[UUID, PledgesTypeSummaries] = {}

        pledges_by_issue: dict[UUID, list[Pledge]] = {}
        for p in all_pledges:
            exist = pledges_by_issue.get(p.issue_id, [])
            exist.append(p)
            pledges_by_issue[p.issue_id] = exist

        for i in issues:
            pledges = pledges_by_issue.get(i.id, [])

            def summary(type: PledgeType) -> FundingPledgesSummary:
                pledges_of_type = [p for p in pledges if p.type == type]
                amount = sum([p.amount for p in pledges_of_type])
                pledgers = [
                    p for p in [Pledger.from_pledge(p) for p in pledges_of_type] if p
                ]

                return FundingPledgesSummary(
                    total=CurrencyAmount(currency="USD", amount=amount),
                    pledgers=pledgers,
                )

            res[i.id] = PledgesTypeSummaries(
                pay_upfront=summary(PledgeType.pay_upfront),
                pay_on_completion=summary(PledgeType.pay_on_completion),
                pay_directly=summary(PledgeType.pay_directly),
            )

        return res


pledge = PledgeService(Pledge)
