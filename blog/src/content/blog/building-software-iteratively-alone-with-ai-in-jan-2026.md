---
title: "Building Software Iteratively Alone with AI - in the beginning of 2026"
excerpt: "AI as abstraction layer for building software iteratively alone. Exploring real-world examples and challenges in early 2026."
publishDate: 2026-01-02
isFeatured: true
tags: ["AI", "Software Development", "2026", "Technology Trends"]
seo:
    title: "State of the Art: Building Software with AI - in the beginning of 2026"
    description: "Exploring the cutting-edge advancements in AI-driven software development as we enter 2026."
---
## DRAFT

Shipping without reading ai-generated code
new level of abstraction

Agents can read and change more code faster than any human can review it

https://www.youtube.com/watch?v=lXUZvyajciY&t=1833s

Let's look at two examples of shipping software with ai without reading it:

One techy shipping (a lot) software with ai without reading it:
https://steipete.me/posts/2025/shipping-at-inference-speed
One non-techy shipping (a lot) software with ai without reading it:
https://x.com/bentossell/status/2006352820140749073

Undeniable positive impact:
- experimentation cycles are much faster => Yes
- Faster iteration on ideas => Yes
- prototyping is way faster => Yes

Building software iteratively alone with ai:
- Non techy: 
  > **Every idea you've ever had can be exercised, can be explored, and it doesn't need to be good.** And you'll learn along the way.
  - Can explore ideas faster. the feedback loop of exploring an idea, getting feedback, and iterating on it is much shorter now.
- Techy:
  > Have rarely a complete picture of what I want to build in my head. He never starts with a complete idea, adn then he expects ai to deliver an output of it.
  > He always starts with a rough idea, and then he needs to shape it and play with it and see how it feels, and the refine it...
  > Often the idea itself  drastically changes while exploring the problem domain.

The non-techy:
- builds prototypes 
- builds "non critical" software (less than 10K users)
- contribute with some improvements to what he calls "real products" that teammates can review and ship
- does a lot of explorations and throws away a lot of what didn't work
He tolerates bugs and issues in his prototypes and he calls them "knowledge gaps".

The techy builds a lot of software alone with ai.

One common practice both share is 
- to build iteratively, starting with a rough idea and refining it as they go along. They both embrace the idea of exploration and learning through building, rather than trying to have a complete picture of what they want to build from the start.
- Just talk to the models, get something working, and then refine it. Keep it simple. They do not have complex ai setups and workflows. => Short prompts
  - The non-techy is even impressive here: he commits to the main directly, never reverts, no PR, no branches, no git worktree, no past sessions, no issue tracker (except for end users reporting bugs). Just build, commit, repeat. and docs in the repo docs/*.md (and let the model write it and name it)
- the disappearance of the IDE

Challenges:
- What’s still hard? Picking the right dependency and framework to set on is something I invest quite some time on. Is this well-maintained? How about peer dependencies? Is it popular = will have enough world knowledge so agents have an easy time? Equally, system design. Will we communicate via web sockets? HTML? What do I put into the server and what into the client? How and which data flows where to where? Often these are things that are a bit harder to explain to a model and where research and thinking pays off.
- building software in team with ai
- communication and alignment has always been a challenge between humans, adding ai to the mix makes it even more complex
- humans still the bottleneck in the process of reviewing, validating, and integrating ai-generated code





Intent matters a lot: Why we are building something, what the goals are, what the constraints are. 




https://x.com/bcherny/status/2007179832300581177


https://x.com/karpathy/status/2004607146781278521?s=20


https://x.com/addyosmani/status/2007899127925854536?s=12&t=rJz-3ilhCTZiNnpOOCegvg
(root: https://x.com/karrisaarinen/status/2007534281011155419)


- speed of development has increased dramatically => No
