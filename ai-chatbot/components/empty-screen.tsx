import { UseChatHelpers } from 'ai/react'

import { Button } from '@/components/ui/button'
import { ExternalLink } from '@/components/external-link'
import { IconArrowRight } from '@/components/ui/icons'

const exampleMessages = [
  {
    heading: 'Onboard New Team Members',
    message: 'Help me understand the current project structure and key components for onboarding: \n'
  },
  {
    heading: 'Write User Stories',
    message: 'Write user stories for the following business goals: \n'
  },
  {
    heading: 'Implement a User Story',
    message: 'Implement the following user story: \n'
  },
  {
    heading: 'Review Code',
    message: `Review the following code snippet and suggest optimizations: \n`
  },
  {
    heading: 'Create a Glossary of Terms',
    message: 'Create a glossary of ubiquitous language terms for our project: \n'
  },
  {
    heading: 'Generate Documentation',
    message: 'Generate technical documentation for the following feature: \n'
  },
]

export function EmptyScreen({ setInput }: Pick<UseChatHelpers, 'setInput'>) {
  return (
    <div className="mx-auto max-w-2xl px-4">
      <div className="rounded-lg border bg-background p-8">
        <h1 className="mb-2 text-lg font-semibold">
          Welcome to umans.ai platform!
        </h1>
        <p className="mb-2 leading-normal text-muted-foreground">
        umans.ai is a multi-AI agent platform designed to help software development teams master complexity and deliver value continuously.
        </p>
        <p className="leading-normal text-muted-foreground">
          You can start a conversation here or try the following examples:
        </p>
        <div className="mt-4 flex flex-col items-start space-y-2">
          {exampleMessages.map((message, index) => (
            <Button
              key={index}
              variant="link"
              className="h-auto p-0 text-base"
              onClick={() => setInput(message.message)}
            >
              <IconArrowRight className="mr-2 text-muted-foreground" />
              {message.heading}
            </Button>
          ))}
        </div>
      </div>
    </div>
  )
}
