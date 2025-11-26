---
title: "AI coding agents and the messy truth about consistency"
excerpt: "Exploring the challenges and strategies for maintaining codebase consistency in the age of AI coding agents."
publishDate: 2025-11-10
updatedDate: 2025-11-10
isFeatured: true
tags: [ "AI", "Engineering", "Consistency" ]
seo:
  title: "AI coding agents and consistency"
  description: "Why consistency still matters when humans and AI code together, and how to keep it."
---

One of the most common complaints I hear about AI coding agents is:

> They helped ship the feature… but now the codebase feels like a patchwork.

And honestly, I get it.

Agents are very good at solving local problems. Sometimes they even surface better patterns than what we had before. But
they also make it easy to introduce yet another way of doing the same thing.

Over time, that hurts.

Not because “AI writes bad code” (even though it does sometimes), but because **AI doesn’t share our conventions by
default**.

Even when we add “be consistent with existing code” to our prompts, it often feels like it barely changes the outcome.

So let’s talk about consistency: why it still matters, what inconsistency actually looks like in a living codebase, and
how we are starting to use agents to manage it instead of making it worse.

## Why consistency still matters

When you don’t have a shared way of doing things (humans or humans + AI), you pay a tax everywhere:

* **Higher cost of change**
  Every change starts with archaeology. You need to reverse-engineer how this part works before touching anything. You
  miss opportunities to reuse helpers, tests, fixtures, tooling… because nothing looks quite the same twice.

* **Higher cognitive load**
  Onboarding is painful. Reading code is full of “wait, why is it done like *this* here?” Each jump between files comes
  with a context switch in your head.

* **Less repeatability**
  If similar problems are solved in different ways, it’s harder to predict the impact of a change or to automate
  refactorings.

That’s what people usually mean when they complain about “AI patchwork”:
not just style differences, but **inconsistent ways of solving the same kind of problem**.

## What is inconsistency, really?

For me, inconsistency is very simple:

> **Doing the same thing in different ways, without a good reason.**

A few examples that keep coming back in real codebases:

* **Validation**
  Some endpoints do manual `if` checks, others use a schema library, others rely on database constraints and hope for
  the best.

* **Async code**
  One module uses callbacks, another uses `.then()`, another uses `async/await`.

* **Time**
  Sometimes you see `new Date()` in the middle of the domain.
  Sometimes there is a `Clock` abstraction.
  Sometimes time is passed around as a string.

* **IDs**
  In one place, IDs come from the database.
  In another, they are generated with a library.
  Elsewhere, someone sprinkled random UUIDs directly in the frontend.

* **Configuration**
  Environment variables are read with `process.env` in some files, through a config module in others, via a DI container
  somewhere else, and hardcoded in tests.

These patterns create cognitive load because **the intent is not obvious**.
A developer reading the code has to ask questions like:

* “Should I use `await` or `.then()` here?”
* “Do I call `new Date()` or inject the `Clock`?”
* “Where is this ID supposed to come from?”
* “How do we read config safely in this part of the code?”

If the answers are not visible in the code or the documentation, every small decision requires archaeology.
And when intent is missing, people tend to add defensive code and speculation, which often makes things more complex
than the inconsistency itself.

## How inconsistency happens and how teams handled it before agents

### How inconsistency appears and sticks

Most inconsistencies do not come from “bad developers”.

They usually come from a mix of:

* Missing shared understanding of how things should be done.
* Decisions that were made verbally but never written anywhere.
* Important conversations that never happened because everyone was rushing to ship.

On top of that, there is the time factor.

A typical pattern looks like this:

1. Someone introduces a new way of doing something. Maybe it is a quick experiment to ship a feature, maybe it is just
   what the agent suggested that day.
2. It works well enough, so it stays.
3. Other people copy what they see locally.
4. Months later, you realise you now have three patterns for the same concern.

In other words, decisions are either missing, or they exist but take a long time to propagate.

### What helped consistent teams before agents

Before AI agents entered the picture, the most stable codebases I saw had one thing in common:
they were good at the loop **decide → record → apply**.

* **Decide**
  The team discusses trade offs and chooses an approach.
  Sometimes this is quite centralised, with a small group of people who own the technical direction.
  Sometimes it is more decentralised and collaborative.
  The structure can vary, but a decision is actually made.

* **Record**
  They write down the decision in a place that is a real source of truth.
  That can be an ADR, a short design note, or a coding guideline with concrete examples.
  The important part is that you can:

    * find the decision, and
    * understand the intent and the motivation behind it.

* **Apply**
  They use building blocks and frameworks that embody these decisions.
  Things like shared modules, base classes, or patterns that make the “right way” the easy way.
  They reinforce this with:

    * pair programming,
    * code reviews,
    * collective ownership practices,
    * sometimes tooling like linters and CI checks.

One important warning here:
if people only copy the pattern without understanding the intent, you get cargo cult.
Cargo cult can be more harmful than inconsistency, because you end up with complex structures nobody can explain.

So for me, the health of a codebase is less about “is everything consistent” and more about:

> Can we see the decisions, the intent, and the building blocks that make those decisions easy to follow?

## How AI agents change the picture

AI agents sit right in the middle of this loop and disturb it in both good and bad ways.

On the risky side:

* They have been trained on a huge variety of styles and architectures.
* By default, they optimise for “solve this prompt here and now”, not “preserve the long term shape of this system”.
* Different models, prompts, and tools used by different people can multiply patterns very quickly.

So if your decide → record → apply loop is weak, agents will happily amplify the inconsistency you already have.

On the opportunity side:

* Agents can read and analyse more code than any human in one sitting.
* They can be fed your existing decisions, guidelines, and examples.
* They can help check how well the codebase follows the conventions you care about.

That leads to a useful question:

> Given our building blocks and architectural rules, how well does this codebase actually follow its own conventions?

This is exactly the angle we are exploring.

## Using agents to work with inconsistency

The way I see it today, agents can join the same loop as humans:

> decide → record → apply

They do not replace it. They help scale it.

### 1. Make the implicit explicit

First step is still human work.

* Capture decisions in short, concrete docs, not just in people’s heads.
* Define the core building blocks of the system and how they are meant to be combined.
* Write coding guidelines with real examples from the codebase.

Then bring agents into that context:

* Feed them these docs and example files.
* Remind them in prompts:

    * “Follow existing patterns in this module.”
    * “Use `Clock` instead of `new Date()` in the domain layer.”
    * “Reuse the existing config module instead of reading `process.env` directly.”

It is simple, but if you skip this step, you basically ask the agent to improvise a style on top of your system.

### 2. Use agents to surface inconsistency

Next, use agents to make inconsistency visible.

Examples of prompts:

* “List the different ways we handle time in this repository.”
* “Show me the patterns we use for async code in this service.”
* “Where and how do we read configuration values?”
* “Give me examples of how we validate input across modules.”

You move from a vague feeling of “this codebase is messy” to a concrete map of where patterns diverge.
That is something a team can actually discuss and decide on.

### 3. Use agents to apply decisions

Finally, once the team decides:

> “From now on, we do it this way.”

Agents can help apply that decision.

For example:

* Refactor one or two files carefully to the new pattern, with tests as safety net.
* Use that as a reference and ask the agent to generalise the change across a wider scope.
* Keep humans in the loop to review, adjust, and stop when things get risky.

This is also where our future experiments live:

* How well do different models follow explicit guidelines and architectural rules when refactoring?
* How far can we push them before they start drifting from the conventions?
* What kind of prompts, context, or tooling make them more reliable collaborators?

We are starting to measure that in practice, not just in theory, and we will share those results in follow up posts.

## Where we go from here

I do not see AI as a magic answer to consistency.
Right now, my working hypothesis is that agents can:

* **Help spot** inconsistencies more systematically.
* **Help spread** good patterns once the team has decided on them.
* **Reduce the cost** of bringing a messy codebase back in shape.

We are currently running experiments around this, for example:

* Using agents to apply explicit guidelines at scale.
* Measuring how well different models follow conventions and architectural rules.
* Comparing instruction following across multiple agent setups, and seeing where they succeed or fail to respect the
  agreed patterns.

We will share concrete metrics, prompts, and results in follow-up posts, so you can see where it works, where it breaks,
and how we design these experiments.

We have opinions, but they are still evolving.
If you are experimenting with similar ideas in your team, I would love to compare notes.

