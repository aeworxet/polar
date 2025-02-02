import { XMarkIcon } from '@heroicons/react/24/outline'
import {
  Account,
  AccountType,
  ResponseError,
  ValidationError,
} from '@polar-sh/sdk'
import { useRouter } from 'next/navigation'
import { api } from 'polarkit'
import { ACCOUNT_TYPE_DISPLAY_NAMES } from 'polarkit/account'
import { getValidationErrorsMap } from 'polarkit/api/errors'
import { CountryPicker, PrimaryButton } from 'polarkit/components/ui/atoms'
import { ChangeEvent, useState } from 'react'
import { ModalBox } from '../Modal'

const SetupAccount = ({
  onClose,
  forOrganizationId,
  forUserId,
  accountTypes,
}: {
  onClose: () => void
  forOrganizationId?: string
  forUserId?: string
  accountTypes: AccountType[]
}) => {
  const router = useRouter()

  const [accountType, setAccountType] = useState<AccountType>(
    AccountType.STRIPE,
  )
  const [openCollectiveSlug, setOpenCollectiveSlug] = useState<string | null>(
    null,
  )
  const [country, setCountry] = useState<string>('US')
  const [validationErrors, setValidationErrors] = useState<
    Record<string, string[]>
  >({})
  const [errorMessage, setErrorMessage] = useState<string | undefined>()

  const [loading, setLoading] = useState(false)

  const resetErrors = () => {
    setErrorMessage(undefined)
    setValidationErrors({})
  }

  const onChangeAccountType = (e: ChangeEvent<HTMLSelectElement>) => {
    resetErrors()
    setAccountType(e.target.value as AccountType)
  }

  const onChangeOpenCollectiveSlug = (e: ChangeEvent<HTMLInputElement>) => {
    resetErrors()
    setOpenCollectiveSlug(e.target.value)
  }

  const onChangeCountry = (countryCode: string) => {
    resetErrors()
    setCountry(countryCode)
  }

  const onConfirm = async () => {
    setLoading(true)

    try {
      const account = await api.accounts.create({
        accountCreate: {
          organization_id: forOrganizationId,
          user_id: forUserId,
          account_type: accountType,
          country,
          ...(openCollectiveSlug
            ? { open_collective_slug: openCollectiveSlug }
            : {}),
        },
      })

      await goToOnboarding(account)
    } catch (e) {
      if (e instanceof ResponseError) {
        const body = await e.response.json()
        if (e.response.status === 422) {
          const validationErrors = body['detail'] as ValidationError[]
          setValidationErrors(getValidationErrorsMap(validationErrors))
        } else if (body['detail']) {
          setErrorMessage(body['detail'])
        }
      }
    } finally {
      setLoading(false)
    }
  }

  const goToOnboarding = async (account: Account) => {
    setLoading(true)

    try {
      const link = await api.accounts.onboardingLink({
        id: account.id,
      })
      window.location.href = link.url
    } catch (e) {
      window.location.reload()
    } finally {
      setLoading(false)
    }
  }

  return (
    <ModalBox className="max-w-[400px]">
      <>
        <div className="flex w-full items-start justify-between">
          <h1 className="text-2xl font-normal">Receive payments</h1>
          <XMarkIcon
            className="dark:hover:text-polar-400 h-6 w-6 cursor-pointer hover:text-gray-500"
            onClick={onClose}
          />
        </div>

        <form className="z-0 flex flex-col space-y-4">
          <div className="space-y-4">
            <div>
              <select
                id="account_type"
                name="account_type"
                onChange={onChangeAccountType}
                className="font-display dark:border-polar-500 block w-full rounded-lg border-gray-200 bg-transparent px-4 py-2 pr-12 shadow-sm transition-colors focus:z-10 focus:border-blue-500 focus:ring-blue-500"
              >
                {accountTypes.map((v: AccountType) => (
                  <option key={v} value={v} selected={v === accountType}>
                    {ACCOUNT_TYPE_DISPLAY_NAMES[v]}
                  </option>
                ))}
              </select>
              {validationErrors.account_type?.map((error) => (
                <p key={error} className="mt-2 text-xs text-red-500">
                  {error}
                </p>
              ))}
            </div>

            {accountType === AccountType.OPEN_COLLECTIVE && (
              <div>
                <div className="relative mt-2">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <span className="font-display dark:text-polar-40 text-gray-500">
                      https://opencollective.com/
                    </span>
                  </div>
                  <input
                    type="text"
                    id="open_collective_slug"
                    name="open_collective_slug"
                    className="font-display dark:border-polar-500 block w-full rounded-lg border-gray-200 bg-transparent py-2 pl-60 shadow-sm transition-colors focus:z-10 focus:border-blue-500 focus:ring-blue-500"
                    value={openCollectiveSlug || ''}
                    onChange={onChangeOpenCollectiveSlug}
                    required
                  />
                </div>
                {validationErrors.open_collective_slug?.map((error) => (
                  <p key={error} className="mt-2 text-xs text-red-500">
                    {error}
                  </p>
                ))}
              </div>
            )}

            <div>
              <CountryPicker onSelectCountry={onChangeCountry} />
              <p className="dark:text-polar-40 mt-2 text-justify text-xs font-medium text-gray-500">
                If this is a personal account, please select your country of
                residence. If this is an organization or business, select the
                country of tax residency.
              </p>
              {validationErrors.country?.map((error) => (
                <p key={error} className="mt-2 text-xs text-red-500">
                  {error}
                </p>
              ))}
            </div>
          </div>

          {errorMessage && (
            <p className="text-xs text-red-500">{errorMessage}</p>
          )}
          {validationErrors.__root__?.map((error) => (
            <p key={error} className="mt-2 text-xs text-red-500">
              {error}
            </p>
          ))}
        </form>

        <div className="md:flex-1"></div>

        <PrimaryButton onClick={onConfirm} loading={loading} disabled={loading}>
          Set up account
        </PrimaryButton>
      </>
    </ModalBox>
  )
}

export default SetupAccount
