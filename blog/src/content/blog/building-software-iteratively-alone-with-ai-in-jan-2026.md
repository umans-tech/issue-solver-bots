---
title: "Shipping Solo With AI Agents Without Reading the Code"
excerpt: "A new abstraction is emerging for solo building: iterate on intent with an AI agent, run, refine, and read little code. What enables it now, and where it breaks."
publishDate: 2026-01-02
isFeatured: true
tags: [ "AI", "Coding Agents", "Agentic Workflows", "Software Engineering", "Testing", "Developer Experience" ]
seo:
  title: "Shipping solo with AI agents without reading code"
  description: "AI is becoming a new abstraction for solo building: iterate on intent, run, refine, read little code. What enables it now, and why teams are harder."
---

If your mental model of coding agents is stuck around May 2025, it is worth updating. The baseline shifts
fast, [even for people who watch the space every day](https://x.com/karpathy/status/2004607146781278521).

Back then, the loop often looked like this: the agent generates code fast, you still have to pull the work back into
your head, and you end up reading diffs more than you want. The agent moves quickly, and by the time you start reading,
it has already moved on.

That pace mismatch is the whole problem. Agents can change more code than a human can comfortably validate. And if you
try to delegate a real change and get a huge pull request back, you are not "reviewing code" anymore. You are reviewing
dozens of silent assumptions and micro decisions the agent made on its own.

So a lot of us parked the idea at: useful for prototypes, maybe for small apps, not a real abstraction.

What feels different now is that, for a growing number of people working alone, the abstraction is starting to hold.

They build by talking to an agent in a CLI, letting it run and iterate, validating through behavior, and reading little
to no code.

## What solo builders are saying, from two sides

Two posts capture this shift well, from two very different profiles:

* Ben Tossell, [How I code with agents, without being "technical"](https://x.com/bentossell/status/2006352820140749073)
* Peter Steinberger, [Shipping at Inference Speed](https://steipete.me/posts/2025/shipping-at-inference-speed)

Ben does not present himself as a traditional engineer. He describes spending an absurd amount of time with an agent in
a terminal, shipping prototypes, throwing many away, and tolerating bugs he calls "knowledge gaps". He does not read the
code. He reads the agent output, watches what it is doing, runs the system, hits issues, and iterates.

Peter Steinberger comes from a more traditional engineering background. He ships a lot of software and is very
comfortable with engineering decisions. Yet his story converges on the same loop: start with a rough idea, shape it by
iteration, and let execution drive the feedback. He also admits he reads far less code than he used to, because the loop
is happening somewhere else.

What I find useful is not the headline. It is the shared behavior:

* They do not start with a complete picture.
* They start with something rough, then explore until it feels right.
* The idea itself often changes along the way.

This is the part many teams claim to do, but rarely do at high speed. The loop compresses so much that exploration
becomes normal again.

One detail from Ben is worth calling out: he explicitly points to end to end tests as something he wants more of,
because he keeps hitting silly bugs that a good executable check would have caught earlier. That fits the overall theme
of these posts: you do not get confidence by reading more code, you get it by tightening feedback.

## Why this feels like a new abstraction

I am not interested in "the end of code" takes. That is not what is happening.

The shift is simpler: the center of gravity moves.

The work is less about writing code directly and more about steering a running system toward intent.

When it works, you are not validating by reading. You are validating by observing behavior, getting grounded feedback,
and asking the agent to fix what reality exposes.

It sounds obvious, but it is a different mental model from "prompt to code". It is "intent to behavior".

It also explains why the interface is often a terminal. Not because terminals are cool. Because the loop is tight:

You ask → the agent changes → the agent runs → reality answers → you iterate.

## What makes this possible now

A year ago, we had impressive models and lots of folklore. Big prompts, complex rituals, custom harnesses.

Now, the enabling ingredients are getting boring, which is a compliment.

Tools are more reliable. Agents are better at using tools without constant guidance. The ecosystem is converging on
shared building blocks: [MCP](https://modelcontextprotocol.io/), plus agent instruction surfaces
like [AGENTS.md](https://agents.md/)
and [Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills). The
practical benefit is simple: less prompt folklore, more repeatable guidance the agent can load when needed.

And yes, the models seem better at the agentic part: planning, executing, noticing feedback, and staying on track across
multiple steps.

Another underrated piece is documentation as context. Both the workflow and the system get easier to iterate on when the
agent also maintains the docs. A simple pattern like keeping living notes in `docs/*.md` gives the agent a stable place
to write down decisions, setup steps, and how things are supposed to work, then update it as the project evolves. It
reduces the need for long prompts and makes the loop more repeatable across sessions.

This matters because it lowers the cost of keeping things simple. You do not need a complicated setup to get real
iteration. You need an agent that can act and check.

## How to make it work without fancy setups

A lot of people get intimidated by the screenshots: multiple panes, custom scripts, special commands, bespoke workflows.

These two posts point to something much simpler, and I think that is the useful message for our audience.

1. Talk to the model in short instructions.
2. Iterate in small steps.
3. Make sure the agent can check by itself.

That third point is the real one. If the agent cannot run, observe, and self correct, you will end up doing the checking
manually, and the abstraction collapses back into reading and babysitting.

This "self check" requirement is also where the next challenge begins, especially once you move from solo work to teams.
It is something we work actively on at Umans.ai too. _wink wink [envs.umans.ai](https://envs.umans.ai)_ 

## Promising, but not solved

Both perspectives are honest about imperfections.

Ben tolerates bugs and calls them knowledge gaps. He does not seem to run a queue, a backlog, or a formal validation
gate. It is exploration first. That is the point.

Peter also does not frame this as a correctness revolution. He frames it as an iteration revolution.

That is important: this is not a claim that everything is safe now. It is a claim that the solo iteration loop is
getting real.

And there are still hard parts that show up immediately once you build anything beyond a toy.

Dependency choice is still hard. Which framework is stable. Which library is well maintained. Which ecosystem is popular
enough that the model has strong prior knowledge. These decisions can make the difference between smooth iteration and
hours of drift.

Architecture and system design are still hard. Where does state live. What goes to the client. What stays on the server.
How data flows. How boundaries are shaped. These are harder to just prompt, and the cost of a poor choice compounds.

Then there is model behavior itself. Karpathy describes this
as ["LLM cognitive deficits"](https://www.dwarkesh.com/i/176425744/llm-cognitive-deficits): models can miss obvious
gaps, over compensate, and produce overly defensive code. That often means extra guards, try catch blocks, and
complexity that make the code feel bloated or harder to reason about. This is not a moral failure. It is a predictable
outcome when intent and constraints are fuzzy.

Which brings us to the real lever.

## Intent is the spec

If you want this abstraction to hold, intent has to be explicit.

* Why are we building this?
* What constraints matter?
* What should never happen?
* What does "good" look like when the system runs?

In solo mode, you can keep intent in your head and correct course quickly. That is why this works so well for one
person.

In team mode, intent has to survive beyond one person. And that is where things get interesting.

## The cliff edge: teams

Solo work is the best case scenario.

The moment you add a team, you reintroduce shared trust, alignment, and governance. Not as bureaucracy, but as a
survival mechanism.

And we hit the same wall again: agents can produce more change than teams can comfortably review. A large pull request
is not just more code. It is more decisions.

So here is what I care about next:

- **Keeping the abstraction:** How do we build with humans who need shared understanding and confidence?
- **Avoiding the bottleneck:** How do we keep validation fast without turning humans into the approval gate again?

That is the follow up article I want to write next.

## References

### Featured field reports

* Peter Steinberger, *Shipping at Inference Speed* (Dec 28, 2025)  
  https://steipete.me/posts/2025/shipping-at-inference-speed
* Ben Tossell, *How I code with agents, without being "technical"* (Dec 31, 2025)  
  X thread: https://x.com/bentossell/status/2006352820140749073  
  Blog version: https://www.bentossell.com/blog/post.html?slug=how-i-code

### Context: the pace of change

* Andrej Karpathy, "I’ve never felt this behind as a programmer…" (Dec 26, 2025)  
  https://x.com/karpathy/status/2004607146781278521

### On "LLM cognitive deficits" and defensive code

* Andrej Karpathy interview, Dwarkesh Patel podcast (full transcript)  
  https://www.dwarkesh.com/p/andrej-karpathy
* Clip reference to the "LLM cognitive deficit" segment (timestamped)  
  https://www.youtube.com/watch?v=lXUZvyajciY&t=1833s

### Acceptance tests as executable specifications

* Dave Farley, *Acceptance testing is the future of programming*  
  https://www.youtube.com/watch?v=NsOUKfzyZiU

### Earlier talks where we discussed the abstraction layer idea

* *The Ultimate Software Crafter* (Crafting Data Science meetup, Jun 25, 2024)  
  Video: https://www.youtube.com/watch?v=Rz1MWIp-oko  
  Slides: https://speakerdeck.com/jcraftsman/the-ultimate-software-crafter-meetup-crafting-data-science
* *Au delà du buzz: IA dans le développement logiciel, assistant ou agent de code* (Nov 2025)  
  Slides: https://speakerdeck.com/jcraftsman/au-dela-du-buzz-lia-dans-le-developpement-logicielle-assistant-ou-agent-de-code
