# Diagrams

This folder stores architecture and design diagrams as `.drawio` (diagrams.net) source files.
For easy viewing in GitHub, each diagram should also be committed as an exported `.svg` (preferred) or `.png`.

## Quick start

### View diagrams (in GitHub)
Open the exported files (`.svg` / `.png`) directly in GitHub for a rendered preview.

### Edit diagrams (in diagrams.net / draw.io)
GitHub does not natively open `.drawio` files in diagrams.net. To edit:

1. Open https://app.diagrams.net/
2. Select **File → Open from → GitHub**
3. Authorize access (if prompted)
4. Browse to this repository and select the `.drawio` file you want to edit
5. Make changes and **Save** back to GitHub (commit to a branch, then open a PR)

## Repository conventions

### File naming
For each diagram, keep both:
- `diagram.drawio` (source of truth)
- `diagram.svg` (rendered preview for GitHub)

Example:
- `Agentic AI.drawio`
- `Agentic AI.svg`

### Export settings (recommended)
When exporting from diagrams.net:
- Prefer **SVG** for crisp rendering in GitHub
- Enable **“Include a copy of my diagram”** (so the `.svg` remains editable if needed)
- Use a consistent page size / scale across diagrams where possible

### Pull request checklist
When a `.drawio` file changes, ensure the PR also includes the updated exported preview:
- [ ] Updated `.drawio` source
- [ ] Updated `.svg`/`.png` export committed alongside it

## Tips

- If you prefer local editing, install the diagrams.net desktop app and open `.drawio` files directly after cloning.
- For larger diagrams, SVG tends to review better in PRs than PNG due to zoom and clarity.
