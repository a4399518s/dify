import type { Fetcher } from 'swr'
import { get, post } from './base'
import type { CommonResponse } from '@/models/common'
import type {
  AiInfo
} from '@/types/msh'
import type { BlockEnum } from '@/app/components/workflow/types'

export const getAiInfo = (url: string) => {
  return get(url, {}, { silent: true }) as Promise<AiInfo>
}
