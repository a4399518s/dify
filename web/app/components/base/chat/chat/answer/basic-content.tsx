import type { FC } from 'react'
import { memo } from 'react'
import type { ChatItem } from '../../types'
import { Markdown } from '@/app/components/base/markdown'
import cn from '@/utils/classnames'

import { WxSubscribeButton } from '@/app/components/base/wx'

type BasicContentProps = {
  item: ChatItem
}
const BasicContent: FC<BasicContentProps> = ({
  item,
}) => {
  const {
    annotation,
    content,
  } = item

  if (annotation?.logAnnotation)
    return <Markdown content={annotation?.logAnnotation.content || ''} />
  if (content.indexOf("---wx---") != -1) {
    let md = content.replace("---wx---", "")
    return (
      <>
        <Markdown
          className={cn(
            item.isError && '!text-[#F04438]',
          )}
          content={md}
        />
        <WxSubscribeButton></WxSubscribeButton>
      </>
    )    
  }
  return (
    <Markdown
      className={cn(
        item.isError && '!text-[#F04438]',
      )}
      content={content}
    />
  )
}

export default memo(BasicContent)
