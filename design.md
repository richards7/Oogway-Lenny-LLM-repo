# Design & UI/UX Specification: The Lenny Growth Assistant

## 1. Design Aesthetics & Visual Philosophy
The Lenny Growth Assistant features a high-end, dark-mode glassmorphic interface inspired by top modern developer tools and AI studios (Linear, Vercel, Anthropic).

### Color Palette (Tailored Dark Theme Tokens)
- **Background Root**: `hsl(224, 25%, 6%)` (Deep slate night)
- **Card / Surface Background**: `hsl(224, 20%, 10%, 0.7)` with `backdrop-filter: blur(16px)`
- **Border Overlay**: `hsla(224, 20%, 25%, 0.4)`
- **Primary Accent**: `hsl(250, 85%, 65%)` (Vibrant Indigo-Violet gradient)
- **Primary Accent Hover**: `hsl(250, 85%, 72%)`
- **Text Main**: `hsl(210, 20%, 98%)`
- **Text Secondary**: `hsl(215, 15%, 65%)`
- **Citation Badge**: `hsl(190, 90%, 25%)` text `hsl(190, 90%, 85%)`

### Typography & Hierarchy
- **Font Family**: 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif
- **Headings**: Semi-bold to Bold, subtle text shine gradient
- **Body Text**: 14px / 1.6 line height for comfortable reading
- **Code & Snippets**: 'JetBrains Mono', 'Fira Code', monospace

---

## 2. Information Architecture & Layout Structure

The app uses a 2-column responsive split workspace layout:

```
┌────────────────────────────────────────────────────────────────────────┐
│  HEADER: App Title | Provider Badge (Ollama/Claude/GPT) | New Chat     │
├──────────────────────────────────────┬─────────────────────────────────┤
│  LEFT PANEL: Chat Workspace          │ RIGHT PANEL: Artifact Viewer    │
│  - Message Stream & History          │ - Tabs: Rendered / View Source  │
│  - Role Badges                       │ - Markdown Engine / Sandboxed   │
│  - Interactive Citation Chips        │   Iframe for HTML               │
│  - Typing / Tool Router Status       │ - Copy / Download Bar           │
│  - Input Bar + Mode Quick Actions    │                                 │
└──────────────────────────────────────┴─────────────────────────────────┘
```

---

## 3. Key Interaction States & Micro-Animations
1. **Tool Classification Indicator**: Displays a glowing badge showing which agent tool was routed (`retrieve_and_answer`, `write_ship30_essay`, `generate_artifact`).
2. **Interactive Citation Expansion**: Clicking a citation badge (`[Source 1: Elena Verna]`) highlights the relevant transcript snippet and displays similarity confidence.
3. **Artifact Viewer Sync**: When the agent generates a Ship 30/30 essay or HTML component artifact, the side panel smoothly slides into view with the rendered content.
4. **Sandboxed HTML Safety**: View source toggle enables inspectable clean code with a clear "Sanitized" security badge.
