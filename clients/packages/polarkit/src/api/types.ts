import {
  IssueRead,
  IssueReferenceRead,
  OrganizationRead,
  PledgeRead,
  RepositoryRead,
} from './client'

export type IssueReadWithRelations = IssueRead & {
  references: IssueReferenceRead[]
  dependents: IssueReadWithRelations[]
  pledges: PledgeRead[]
  organization: OrganizationRead
  repository: RepositoryRead
}