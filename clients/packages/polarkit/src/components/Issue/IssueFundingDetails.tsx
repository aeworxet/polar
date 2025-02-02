import { CurrencyAmount, Issue, PledgesTypeSummaries } from '@polar-sh/sdk'
import FundingPill from './FundingPill'
import PledgeSummaryPill from './PledgeSummaryPill'
import PublicRewardPill from './PublicRewardPill'

interface IssueFundingDetailsProps {
  issue: Issue
  total: CurrencyAmount
  fundingGoal?: CurrencyAmount
  pledgesSummaries: PledgesTypeSummaries
  showLogo?: boolean
  showStatus?: boolean
  summaryRight?: React.ReactElement
}

const IssueFundingDetails: React.FC<IssueFundingDetailsProps> = ({
  issue,
  total,
  fundingGoal,
  pledgesSummaries,
}) => {
  const { pay_upfront, pay_on_completion } = pledgesSummaries
  return (
    <div className="flex flex-col items-center gap-4 md:flex-row">
      <FundingPill total={total} goal={fundingGoal} />

      <div className="flex flex-row gap-4">
        {pay_upfront.total.amount > 0 && (
          <PledgeSummaryPill.Funded summary={pay_upfront} />
        )}

        {pay_on_completion.total.amount > 0 && (
          <PledgeSummaryPill.Pledged summary={pay_on_completion} />
        )}
      </div>

      {issue.upfront_split_to_contributors && (
        <PublicRewardPill percent={issue.upfront_split_to_contributors} />
      )}
    </div>
  )
}

export default IssueFundingDetails
