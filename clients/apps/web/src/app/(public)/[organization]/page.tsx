import OrganizationPublicPage from '@/components/Organization/OrganizationPublicPage'
import PageNotFound from '@/components/Shared/PageNotFound'
import {
  ListFundingSortBy,
  Organization,
  Platforms,
  ResponseError,
} from '@polar-sh/sdk'
import type { Metadata, ResolvingMetadata } from 'next'
import { notFound } from 'next/navigation'
import { api } from 'polarkit/api'

const cacheConfig = {
  next: {
    revalidate: 30, // 30 seconds
  },
}

export async function generateMetadata(
  {
    params,
  }: {
    params: { organization: string }
  },
  parent: ResolvingMetadata,
): Promise<Metadata> {
  let organization: Organization | undefined

  try {
    organization = await api.organizations.lookup(
      {
        platform: Platforms.GITHUB,
        organizationName: params.organization,
      },
      cacheConfig,
    )
  } catch (e) {
    if (e instanceof ResponseError && e.response.status === 404) {
      notFound()
    }
  }

  if (!organization) {
    notFound()
  }

  return {
    title: `${organization.name}`, // " | Polar is added by the template"
    openGraph: {
      title: `${organization.name} seeks funding for issues`,
      description: `${organization.name} seeks funding for issues on Polar`,
      siteName: 'Polar',

      images: [
        {
          url: `https://polar.sh/og?org=${organization.name}`,
          width: 1200,
          height: 630,
        },
      ],
    },
    twitter: {
      images: [
        {
          url: `https://polar.sh/og?org=${organization.name}`,
          width: 1200,
          height: 630,
          alt: `${organization.name} seeks funding for issues`,
        },
      ],
      card: 'summary_large_image',
      title: `${organization.name} seeks funding for issues`,
      description: `${organization.name} seeks funding for issues on Polar`,
    },
  }
}

export default async function Page({
  params,
}: {
  params: { organization: string }
}) {
  const organization = await api.organizations.lookup(
    {
      platform: Platforms.GITHUB,
      organizationName: params.organization,
    },
    cacheConfig,
  )

  const repositories = await api.repositories.search(
    {
      platform: Platforms.GITHUB,
      organizationName: params.organization,
    },
    cacheConfig,
  )

  const issuesFunding = await api.funding.search(
    {
      platform: Platforms.GITHUB,
      organizationName: params.organization,
      badged: true,
      closed: false,
      sorting: [
        ListFundingSortBy.MOST_FUNDED,
        ListFundingSortBy.MOST_ENGAGEMENT,
        ListFundingSortBy.NEWEST,
      ],
      limit: 20,
    },
    cacheConfig,
  )

  const totalIssueCount = issuesFunding.pagination.total_count

  if (
    organization === undefined ||
    repositories === undefined ||
    totalIssueCount === undefined
  ) {
    return <PageNotFound />
  }

  return (
    <>
      <OrganizationPublicPage
        organization={organization}
        repositories={repositories.items || []}
        issuesFunding={issuesFunding.items || []}
        totalIssueCount={totalIssueCount}
      />
    </>
  )
}
