'use client'
import { useRouter, useSearchParams } from 'next/navigation'
import type { FC } from 'react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Lock01 } from '@/app/components/base/icons/src/vender/solid/security'
import Toast from '@/app/components/base/toast'
import classNames from '@/utils/classnames'
import style from '../page.module.css'
import { getUserOAuth2SSOUrl, getUserOIDCSSOUrl, getUserSAMLSSOUrl } from '@/service/sso'
import Button from '@/app/components/base/button'
import { apiPrefix } from '@/config'
import { SSOProtocol } from '@/types/feature'
import { getPurifyHref } from '@/utils'

type WxAuthProps = {

}

const WxAuth: FC<WxAuthProps> = ({
}) => {
  const router = useRouter()
  const { t } = useTranslation()
  const searchParams = useSearchParams()
  const tenant_names = decodeURIComponent(searchParams.get('tenant_names') || '')

  const [isLoading, setIsLoading] = useState(false)

  const handleWxLogin = () => {
    setIsLoading(true)
    
    getUserOAuth2SSOUrl(tenant_names).then((res) => {
      document.cookie = `user-oauth2-state=${res.state}`
      router.push(res.url)
    }).finally(() => {
      setIsLoading(false)
    })
    setIsLoading(false)
  }
  
  const getOAuthLink = (href: string) => {
    const url = getPurifyHref(`${apiPrefix}${href}`)
    if (searchParams.has('tenant_names'))
      return `${url}?${searchParams.toString()}`

    return url
  }

  return (
    <a href={getOAuthLink('/oauth/login/wx')}>
      <Button
        className='w-full'
      >
        <>
          <span className={
            classNames(
              style.wxIcon,
              'w-5 h-5 mr-2',
            )
          } />
          <span className="truncate">{t('login.withWx')}</span>
        </>
      </Button>
    </a>
  )
}

export default WxAuth
