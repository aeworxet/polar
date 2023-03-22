import { type PledgeResources } from 'polarkit/api/client'
import { WhiteCard } from 'polarkit/components/ui/Cards'
import IssueCard from './IssueCard'
import PledgeForm from './PledgeForm'
import RepositoryCard from './RepositoryCard'

const Pledge = ({
  organization,
  repository,
  issue,
  query,
}: PledgeResources & {
  query: any // TODO: Investigate & fix type
}) => {
  return (
    <>
      <div className="my-14 flex flex-col">
        <WhiteCard
          className="flex flex-row items-stretch p-2 text-center"
          padding={false}
        >
          <div className="w-1/2">
            <IssueCard issue={issue} />
          </div>
          <div className="w-1/2 text-left">
            <div className="py-5 px-6">
              <PledgeForm
                organization={organization}
                repository={repository}
                issue={issue}
                query={query}
              />
            </div>
          </div>
        </WhiteCard>
        <RepositoryCard organization={organization} repository={repository} />
      </div>
    </>
  )
}

export default Pledge