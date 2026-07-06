---
name: Kinetic Logic
colors:
  surface: '#fcf8ff'
  surface-dim: '#dcd8e5'
  surface-bright: '#fcf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f2ff'
  surface-container: '#f0ecf9'
  surface-container-high: '#eae6f4'
  surface-container-highest: '#e4e1ee'
  on-surface: '#1b1b24'
  on-surface-variant: '#464555'
  inverse-surface: '#302f39'
  inverse-on-surface: '#f3effc'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#0058be'
  on-secondary: '#ffffff'
  secondary-container: '#2170e4'
  on-secondary-container: '#fefcff'
  tertiary: '#7e3000'
  on-tertiary: '#ffffff'
  tertiary-container: '#a44100'
  on-tertiary-container: '#ffd2be'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#ffdbcc'
  tertiary-fixed-dim: '#ffb695'
  on-tertiary-fixed: '#351000'
  on-tertiary-fixed-variant: '#7b2f00'
  background: '#fcf8ff'
  on-background: '#1b1b24'
  surface-variant: '#e4e1ee'
typography:
  display:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  mono:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-margin: 24px
  gutter: 16px
  sidebar-width: 240px
  density-compact: 4px
  density-comfortable: 12px
---

## Brand & Style

The design system is engineered for high-velocity software teams who require a tool that balances dense information architecture with visual serenity. The brand personality is **productive, reliable, and elegant**, favoring utility over decorative flourish.

The aesthetic follows a **Modern Minimalist** movement with a "Developer-First" ethos. It prioritizes clarity, rapid scanning, and functional hierarchy. By utilizing ample white space within components and tight, disciplined spacing between them, the UI remains breathable despite the high data density required for complex project management. 

Visual signals are intentional: color is used sparingly to denote action or status, while the interface itself recedes to keep the user's focus entirely on their tasks and workflows.

## Colors

The palette is anchored by a deep **Primary Indigo**, used for primary actions and key brand touchpoints. A **Secondary Blue** provides support for interactive states and secondary navigational elements. 

The neutral scale is critical for this system's professional tone:
- **Slate Grays (#1E293B, #64748B):** Used for primary and secondary text to ensure high legibility without the harshness of pure black.
- **Soft Gray Backgrounds (#F8FAFC):** Employed for the main application canvas to reduce eye strain during long working sessions.
- **Pure White (#FFFFFF):** Reserved for elevated surfaces like cards, modals, and input fields to create a clear "layer" between the app frame and the content.
- **Success/Warning/Error:** Utilize standard utility colors (Emerald, Amber, Rose) but desaturated to match the professional Slate palette.

## Typography

Typography is the backbone of this design system. We use **Inter** for its exceptional legibility and neutral, systematic appearance. For technical metadata (Issue IDs, Commit Hashes, Labels), we introduce **Geist** to provide a distinct "developer-centric" texture that separates data from prose.

- **Scale:** We utilize a tight typographic scale. Most interface text lives at 14px (`body-md`) and 13px (`body-sm`) to allow for high information density.
- **Letter Spacing:** Headlines use slight negative tracking to feel tighter and more authoritative.
- **Labels:** Small labels and tags should always be rendered in `label-md` or `mono` to distinguish them from interactive text links.

## Layout & Spacing

The design system employs a **Fluid-Fixed Hybrid Grid**. The main navigation sidebar is fixed, while the content canvas scales fluidly to maximize screen real estate for Kanban boards and Backlogs.

- **Spacing Rhythm:** Based on a 4px baseline grid. Internal component padding should follow `8px`, `12px`, or `16px` increments.
- **Information Density:** Support for a "Compact" mode where vertical padding is reduced by 50% for power users managing hundreds of issues.
- **Breakpoints:**
  - **Desktop (1280px+):** Full sidebar, multi-column board views.
  - **Tablet (768px - 1279px):** Collapsed sidebar (icons only), filtered list views.
  - **Mobile (<767px):** Bottom navigation, single-column task stack, simplified header.

## Elevation & Depth

This design system uses a **Tonal Layering** approach combined with **Ambient Shadows** to create a focused hierarchy without visual clutter.

- **Level 0 (Base):** The app background (`#F8FAFC`).
- **Level 1 (Surface):** Cards, Sidebar, and Header. These use a 1px border (`#E2E8F0`) to define their boundaries instead of heavy shadows.
- **Level 2 (Interaction):** Hovered items or active selection. Use a very soft, diffused shadow: `0px 4px 12px rgba(30, 41, 59, 0.05)`.
- **Level 3 (Overlay):** Modals, Dropdowns, and Popovers. These require a more distinct shadow to separate them from the work surface: `0px 12px 24px rgba(30, 41, 59, 0.1)`.

## Shapes

The shape language is disciplined and consistent. A **Rounded (2)** setting is applied across the system to soften the technical nature of the tool while maintaining a professional structure.

- **Standard Elements (8px):** Buttons, Input fields, and Cards. This provides a modern, approachable feel.
- **Large Elements (16px):** Modals and large empty-state containers.
- **Status Indicators:** Use 4px (Soft) roundedness or full pill-shapes for status badges (e.g., "In Progress") to differentiate them from interactive buttons.

## Components

### Buttons
- **Primary:** Solid `#4F46E5` with white text. Subtle 8px rounded corners.
- **Secondary:** White surface with `#E2E8F0` border and `#1E293B` text. 
- **Ghost:** No border or background. Becomes `#F1F5F9` on hover. Used for low-priority actions in toolbars.

### Input Fields
- Always include a 1px border. On focus, the border changes to Primary Indigo with a soft 3px outer glow (ring).
- Use `body-md` for input text and `label-md` for floating or top-aligned labels.

### Cards & Issue Tiles
- White background, 1px Slate border. 
- Internal padding of 12px for high density.
- On drag, increase elevation to Level 3 and add a 2px Primary Indigo left-border highlight.

### Chips & Badges
- Used for Tags and Statuses. Use a "Subtle" style: light background tints of the status color with high-contrast text (e.g., light blue background with dark blue text).

### Navigation
- **Sidebar:** Dark theme variant using Slate Grays or a clean Light theme. Active states should be marked by a vertical 3px line on the left and a slight background tint change.

### Data Tables
- Header row in `#F8FAFC`, text in `label-md` uppercase.
- Row hover state: `#F1F5F9`.