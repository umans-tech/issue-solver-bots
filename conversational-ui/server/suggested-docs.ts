export function getSuggestedDocPrompts(): Record<
  string,
  { title: string; prompt: string }
> {
  return {
    'architecture.md': {
      title: 'Architecture Overview',
      prompt:
        'Summarize components, interactions, and key data flows. Make implicit intent explicit, note integrations/constraints, and include a Mermaid flowchart styled like C4 to illustrate relationships.',
    },
    'onboarding_quickstart.md': {
      title: 'Onboarding Quickstart',
      prompt:
        'Create a newcomer-friendly setup guide: prerequisites, install steps, commands to run the project/tests, common scripts, environment variables, and simple diagrams if helpful. Cite file paths.',
    },
    'glossary.md': {
      title: 'Project Glossary',
      prompt:
        'Write an alphabetical glossary of project terminology (acronyms, key modules, data stores). Use plain language, cite file paths where each term appears, note relationships/dependencies, and call out whether the term is internal-only or user-facing.',
    },
    'domain_events_glossary.md': {
      title: 'Domain Events Glossary',
      prompt:
        'Produce a precise glossary of domain events using only evidence from the repo. Explain when each event fires, payload shape, producers/consumers, and cite file paths. No speculation.',
    },
  };
}
