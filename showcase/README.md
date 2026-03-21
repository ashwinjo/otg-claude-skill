# Claude Skills Showcase

A single-page website showcasing Claude Skill development for the KENG/OTG ecosystem. Designed for video presentations to upper management.

## Quick Start

### Option 1: Open directly in browser

```bash
open showcase/index.html
```

Or double-click `index.html` in Finder.

### Option 2: Serve locally (recommended for video)

```bash
cd showcase
npx serve .
```

Then open http://localhost:3000 in your browser.

## Video Recording Tips

1. **Full-screen**: Press F11 (or Cmd+Shift+F) for a clean capture without browser chrome.
2. **Scroll pace**: Scroll slowly through each section; pause on skill cards and the workflow diagram.
3. **Suggested script** (2–3 minutes):
   - Intro: Who you are, what Claude Skills are
   - Skills overview: Walk through the 5 skill cards
   - Workflow: Explain the end-to-end flow (IxNetwork → OTG → Snappi → Run)
   - Business value: Migration path, faster test creation, automation, licensing
   - Close: Invite questions or schedule a demo
4. **Test first**: Run `open showcase/index.html` or `npx serve showcase` before recording to ensure the Mermaid diagram renders correctly.

## Customization

Edit `index.html` to update:

- **Name**: Search for "Ashwin Joshi" in the hero section
- **Job title**: Adjust the tagline or value statement
- **Contact CTA**: Update the `href` in the Contact section (default: `mailto:your.email@keysight.com`)

## Deployment (optional)

To host on GitHub Pages:

1. Push the `showcase` folder to your repo
2. In repo Settings → Pages, set source to the branch and folder containing `showcase`
3. The site will be available at `https://<username>.github.io/<repo>/showcase/`
