---
name: read-safety-language-interaction-rules
description: >-
  Read-only: English-first communication policy for all skills and AskQuestion flows.
  Use English by default and switch only when the user explicitly requests another full-language response.
---
# Internal: Language interaction rules (`read-safety-language-interaction-rules`)

**Read-only policy library.** This is the canonical language rule for all skill-driven interactions in this repository.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Core policy

1. **Default language is English** for all assistant messages.
2. **Q&A and AskQuestion content must also be English by default** (prompts, options, labels, follow-up text).
3. A **full response in another language** is allowed only when the user explicitly asks for that language.
4. Non-English words are allowed only when they are:
   - quoted user-provided text,
   - canonical proper nouns, product names, APIs, commands, or file names,
   - unavoidable domain-specific terms with no clear English substitute.
5. If language intent is ambiguous, ask a concise clarification question in English.

## AskQuestion language (normative)

- **Always English** for `AskQuestion` **prompt**, **option labels**, and **`additionalSuggestion`** text unless the user explicitly requested another full-language response in this thread.
- **Never** localize Q&A to Portuguese, Spanish, or any other language based on user locale, OS settings, prior chat language, or inferred preference.
- When the user writes in another language but does not ask for a full non-English response, reply in **English** (you may quote their wording when needed).

## Practical guidance

- Keep one language per response unless the user explicitly requests bilingual output.
- Prefer English option labels for finite-choice prompts (`Abort`, `Proceed`, `No`, `Yes`, `Done`, `Not now`).
- Preserve exact command/code syntax even when surrounding prose is in English.

## Do not

- Mix languages by default in the same response.
- Use non-English AskQuestion options without explicit user request.
- Assume language based on locale, OS region, or prior mixed-language examples.
- Put Portuguese (or other non-English) labels in structured Q&A when the user did not explicitly request that language.

## Consumers

All public and internal `SKILL.md` files in this repository should reference this policy before any workflow-specific orchestration.
