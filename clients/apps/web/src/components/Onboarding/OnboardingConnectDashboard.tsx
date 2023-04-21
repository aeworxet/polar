import { PlusIcon } from '@heroicons/react/24/solid'
import Image from 'next/image'
import { CONFIG } from 'polarkit'
import { PrimaryButton } from 'polarkit/components/ui'
import { useStore } from 'polarkit/store'
import { classNames } from 'polarkit/utils'
import { MouseEvent, useEffect, useState } from 'react'
import screenshot from './ScreenshotDashboard.png'

const OnboardingConnectPersonalDashboard = () => {
  const isSkipped = useStore((store) => store.onboardingDashboardSkip)
  const setIsSkipped = useStore((store) => store.setOnboardingDashboardSkip)

  const hideDashboardBanner = (e: MouseEvent<HTMLButtonElement>) => {
    e.preventDefault()
    setIsSkipped(true)
  }

  const [show, setShow] = useState(false)

  useEffect(() => {
    setShow(!isSkipped)
  }, [isSkipped])

  if (!show) {
    return <></>
  }

  return (
    <>
      <div
        className={classNames(
          'flex-start flex flex-row overflow-hidden rounded-lg bg-white shadow',
        )}
      >
        <div className="flex-1">
          <div className="flex h-full flex-col space-y-4 p-6">
            <h2 className="text-xl text-black">
              Track and pledge issues in your dependencies
            </h2>
            <p className="flex-1 text-sm text-gray-500">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec vel
              congue nisi. Curabitur venenatis maximus ex, eu rutrum lacus
              ornare et.
            </p>
            <div className="flex items-center justify-between gap-4 lg:justify-start">
              <PrimaryButton
                color="blue"
                fullWidth={false}
                onClick={() => {
                  window.open(CONFIG.GITHUB_INSTALLATION_URL, '_blank')
                }}
              >
                <PlusIcon className="h-6 w-6" />
                <span>Connect a repository</span>
              </PrimaryButton>
              <button
                type="button"
                className="text-md text-blue-600"
                onClick={hideDashboardBanner}
              >
                Skip
              </button>
            </div>
          </div>
        </div>
        <div className="hidden flex-1 lg:block">
          <Image
            src={screenshot}
            alt="Polar dashboard screenshot"
            className="w-full"
          />
        </div>
      </div>
    </>
  )
}

export default OnboardingConnectPersonalDashboard