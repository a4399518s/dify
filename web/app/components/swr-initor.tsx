'use client'

import { SWRConfig } from 'swr'
import { useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { fetchSetupStatus } from '@/service/common'

type SwrInitorProps = {
  children: ReactNode
}
const SwrInitor = ({
  children,
}: SwrInitorProps) => {
  const router = useRouter()
  const searchParams = useSearchParams()
  const consoleToken = decodeURIComponent(searchParams.get('access_token') || '')
  const refreshToken = decodeURIComponent(searchParams.get('refresh_token') || '')
  const consoleTokenFromLocalStorage = localStorage?.getItem('console_token')
  const refreshTokenFromLocalStorage = localStorage?.getItem('refresh_token')
  const pathname = usePathname()
  const [init, setInit] = useState(false)

  const isSetupFinished = useCallback(async () => {
    try {
      if (localStorage.getItem('setup_status') === 'finished')
        return true
      const setUpStatus = await fetchSetupStatus()
      if (setUpStatus.step !== 'finished') {
        localStorage.removeItem('setup_status')
        return false
      }
      localStorage.setItem('setup_status', 'finished')
      return true
    }
    catch (error) {
      console.error(error)
      return false
    }
  }, [])

  useEffect(() => {
    (async () => {
      try {
        const isFinished = await isSetupFinished()
        if (!isFinished) {
          router.replace('/install')
          return
        }
        if (!((consoleToken && refreshToken) || (consoleTokenFromLocalStorage && refreshTokenFromLocalStorage))) {
          localStorage.setItem('signin_path', location.pathname)
          router.replace('/signin')
          return
        }else{
          const signin_path = localStorage.getItem('signin_path')
          if (signin_path){
            localStorage.removeItem('signin_path')
            location.href = signin_path;
          }          
        }
        if (searchParams.has('access_token') || searchParams.has('refresh_token')) {
          consoleToken && localStorage.setItem('console_token', consoleToken)
          refreshToken && localStorage.setItem('refresh_token', refreshToken)
          router.replace(pathname)
        }
        setInit(true)
        const sharedToken = localStorage.getItem("sharedToken");
        if (sharedToken) {
          if(location.pathname.startsWith("/chat")){
            localStorage.removeItem("sharedToken");
          }          
          location.href = `/chat/${sharedToken}`;
          // router.replace(`/chat/${sharedToken}`);
          return;
        }
      }catch (error) {
        debugger
        router.replace('/signin')
      }
    })()
  }, [isSetupFinished, router, pathname, searchParams, consoleToken, refreshToken, consoleTokenFromLocalStorage, refreshTokenFromLocalStorage])

  return init
    ? (
      <SWRConfig value={{
        shouldRetryOnError: false,
        revalidateOnFocus: false,
      }}>
        {children}
      </SWRConfig>
    )
    : null
}

export default SwrInitor
