![badge-labs](https://user-images.githubusercontent.com/327285/230928932-7c75f8ed-e57b-41db-9fb7-a292a13a1e58.svg)

# AI Reference Architecture Library

This project consists of a collection of FSI-specific AI reference architectures. The library is part of the larger **AI Governance Framework** ecosystem and will both leverage, and be leveraged by, other framework components. Each architecture is designed and curated by a representative pool of professionals from FSIs, system integrators, and technology providers, and will be externally validated by a small group of AI domain experts.

Each architecture will be threat-modelled, with risks and mitigations taken from the AI Governance Framework catalogue, providing a practical and unified view of the applicable security baseline to design, deploy, and operate the system within agreed risk tolerances.

It is critical for the project that our output is usable and applicable to the FSI vertical. To ensure collaboration is effective, industry-standard, and unambiguous, we will establish the following guardrails:

1. Rigour in definitions
2. Agreement on naming conventions (e.g., “risk” vs “threat”)
3. Agreement on architecture layers (e.g., data, inference, agent), components within them, and data flows

## Ways of Working

We agreed that a visual tool that enables collaboration makes the most sense to start with. **draw.io** (diagrams.net) appears to be the best choice, as it is commonly used within FSIs. We will start this way, but unambiguous definitions and naming conventions will also be captured in individual files within the appropriate sub-folders.

Each architecture (with a shortcut to draw.io) will be stored in a subfolder of the main repository. At this stage it is unclear whether further folder nesting will be required (e.g., AI category as the main folder, and individual architectures as subfolders).

Threat modelling will be performed on the architecture itself in a user-friendly way.  


**Example**

<img width="573" height="438" alt="example-visual-threat-model" src="https://github.com/user-attachments/assets/73547b46-040a-4b15-a52c-e330bd2a3b9d" />  


When deemed appropriate, both architectures and associated threat models will be codified in **CALM** to ensure reusability across the **FINOS** member base that uses it.

## Roadmap

Identify and document:

1. Key definitions (layers, components, etc.) — **November 2025**
2. A naming convention (this may require working with other projects such as the AI Governance Framework catalogue) — **November 2025**
3. The sequence of AI systems we want to design — **December 2025**:
   - Single-agent agentic AI
   - Multi-agent agentic AI
   - …

Any actual design work will begin in **January 2026**.

## Contributing

**All commits** must be signed with a DCO signature to avoid being flagged by the DCO Bot. This means that your commit log message must contain a line that looks like the following one, with your actual name and email address:

```
Signed-off-by: John Doe <john.doe@example.com>
```

Adding the `-s` flag to your `git commit` will add that line automatically. You can also add it manually as part of your commit log message or add it afterwards with `git commit --amend -s`.

See [CONTRIBUTING.md](./.github/CONTRIBUTING.md) for more information

### Helpful DCO Resources
- [Git Tools - Signing Your Work](https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work)
- [Signing commits
](https://docs.github.com/en/github/authenticating-to-github/signing-commits)

## License

Copyright 2025 FINOS

Distributed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

SPDX-License-Identifier: [Apache-2.0](https://spdx.org/licenses/Apache-2.0)
