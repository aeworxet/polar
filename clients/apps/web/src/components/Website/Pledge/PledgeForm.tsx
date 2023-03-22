import { Elements } from '@stripe/react-stripe-js'
import { loadStripe } from '@stripe/stripe-js/pure'
import { api } from 'polarkit/api'
import { type PledgeRead, type PledgeResources } from 'polarkit/api/client'
import PrimaryButton from 'polarkit/components/ui/PrimaryButton'
import { CONFIG } from 'polarkit/config'
import { getCentsInDollarString } from 'polarkit/utils'
import { useEffect, useState } from 'react'
import PaymentForm from './PaymentForm'

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_KEY)

const PledgeForm = ({
  organization,
  repository,
  issue,
  query,
}: PledgeResources & {
  query: any // TODO: Investigate & fix type
}) => {
  const [pledge, setPledge] = useState<PledgeRead | null>(null)
  const [amount, setAmount] = useState(0)
  const [email, setEmail] = useState('')
  const [errorMessage, setErrorMessage] = useState(null)
  const [isSyncing, setSyncing] = useState(false)

  const MINIMUM_PLEDGE = CONFIG.MINIMUM_PLEDGE_AMOUNT

  const validateEmail = (email: string) => {
    return email.match(/^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/)
  }

  const createPledge = async () => {
    return await api.pledges.createPledge({
      platform: organization.platform,
      orgName: organization.name,
      repoName: repository.name,
      number: issue.number,
      requestBody: {
        issue_id: issue.id,
        amount: amount,
        email: email,
      },
    })
  }

  const updatePledge = async () => {
    return await api.pledges.updatePledge({
      platform: organization.platform,
      orgName: organization.name,
      repoName: repository.name,
      number: issue.number,
      pledgeId: pledge.id,
      requestBody: {
        amount: amount,
        email: email,
      },
    })
  }

  const shouldSynchronizePledge = () => {
    if (amount < MINIMUM_PLEDGE) {
      return false
    }

    // Always sync in case of valid amount and either 1) updated amount or 2) no prior pledge
    if (!pledge || pledge.amount !== amount) {
      return true
    }

    // Otherwise, only sync if email has changed (and is valid)
    return pledge.email !== email && validateEmail(email)
  }

  const synchronizePledge = async () => {
    if (!shouldSynchronizePledge()) {
      return
    }

    setSyncing(true)
    let updatedPledge: PledgeRead
    if (!pledge) {
      updatedPledge = await createPledge()
    } else {
      updatedPledge = await updatePledge()
    }

    if (updatedPledge) {
      setPledge(updatedPledge)
    }
    setSyncing(false)
  }

  const onAmountChange = (event) => {
    const amount = parseInt(event.target.value)
    if (isNaN(amount)) {
      setErrorMessage('Please enter a valid amount')
      return
    }
    const amountInCents = amount * 100

    if (amountInCents < MINIMUM_PLEDGE) {
      setErrorMessage(
        `Minimum amount is ${getCentsInDollarString(MINIMUM_PLEDGE)}`,
      )
      return
    }

    setErrorMessage(null)
    setAmount(amountInCents)
  }

  const onEmailChange = (event) => {
    const email = event.target.value
    setEmail(email)
  }

  // Debounce synchronization of pledge
  useEffect(() => {
    const sync = setTimeout(synchronizePledge, 500)

    return () => clearTimeout(sync)
  }, [amount, email])

  return (
    <>
      <form className="flex flex-col">
        <label htmlFor="amount" className="text-sm font-medium text-gray-600">
          Choose amount to pledge
        </label>
        <div className="mt-3 flex flex-row items-center space-x-4">
          <div className="relative w-2/3">
            <input
              type="text"
              id="amount"
              name="amount"
              className="block w-full rounded-md border-gray-200 py-3 px-4 pl-9 pr-16 text-sm shadow-sm focus:z-10 focus:border-blue-500 focus:ring-blue-500"
              onChange={onAmountChange}
              onBlur={onAmountChange}
              placeholder={getCentsInDollarString(MINIMUM_PLEDGE)}
            />
            <div className="pointer-events-none absolute inset-y-0 left-0 z-20 flex items-center pl-4">
              <span className="text-gray-500">$</span>
            </div>
            <div className="pointer-events-none absolute inset-y-0 right-0 z-20 flex items-center pr-4">
              <span className="text-gray-500">USD</span>
            </div>
          </div>
          <p className="w-1/3 text-xs text-gray-500">
            Minimum is ${getCentsInDollarString(MINIMUM_PLEDGE)}
          </p>
        </div>

        <label
          htmlFor="email"
          className="mt-5 mb-2 text-sm font-medium text-gray-600"
        >
          Contact details
        </label>
        <input
          type="email"
          id="email"
          onChange={onEmailChange}
          onBlur={onEmailChange}
          className="block w-full rounded-md border-gray-200 py-3 px-4 text-sm shadow-sm focus:z-10 focus:border-blue-500 focus:ring-blue-500"
        />

        {pledge && (
          <Elements
            stripe={stripePromise}
            options={{
              clientSecret: pledge.client_secret,
            }}
          >
            <PaymentForm
              pledge={pledge}
              isSyncing={isSyncing}
              setSyncing={setSyncing}
              setErrorMessage={setErrorMessage}
            />
          </Elements>
        )}

        {/*
         * Unfortunately, we need to have this button (disabled) by default and then
         * remove it once Stripe is initiated. Since we cannot (in an easy/nice way)
         * manage the submission outside of the Stripe Elements context.
         */}
        {!pledge && (
          <div className="mt-6">
            <PrimaryButton disabled={true} loading={isSyncing}>
              Pledge ${getCentsInDollarString(MINIMUM_PLEDGE)}
            </PrimaryButton>
          </div>
        )}

        {errorMessage && <div>{errorMessage}</div>}
      </form>
    </>
  )
}
export default PledgeForm