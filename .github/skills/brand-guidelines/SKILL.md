---
name: brand-guidelines
description: Applies SchoolPadi's official brand colors, typography, and design tokens to any UI artifact in this school management SaaS. Use it when brand colors, style guidelines, visual formatting, or design standards apply to new or existing components, pages, emails, or templates.
---

# SchoolPadi — Brand & Design System

## Overview

SchoolPadi is a multi-tenant SaaS school management platform. Its visual identity operates on **two layers**:

1. **Platform brand** — fixed system-wide chrome (admin UI, auth pages, emails, error pages)
2. **School brand** — per-tenant customizable primary/secondary color pair injected from `SchoolInfo`

Always respect both layers. Platform chrome uses the SchoolPadi system tokens. School-facing public pages may override via CSS variables driven by the tenant's saved colors.

---

## 1. Core Platform Palette

### Primary Brand (App UI & CTA)

| Token | Light mode | Dark mode | Usage |
|---|---|---|---|
| `--primary-brand` | `#4361ee` | `#4cc9f0` | Buttons, active states, links, loader bar |
| `--primary-accent` | `#3a0ca3` | — | Pressed states, deep accents |
| `--secondary-brand` | `#4cc9f0` | — | Gradient pairs, highlights |

Primary gradient (CTA buttons, hero accents):
```css
linear-gradient(135deg, #4361ee 0%, #4cc9f0 100%)
```

### Admin UI — Violet System (dashboard, sidebar, cards)

| Token | Value |
|---|---|
| `--admin-primary` | `#7c3aed` |
| `--admin-primary-light` | `#a78bfa` |
| `--admin-primary-dark` | `#6d28d9` |

Soft gradient utility (card backgrounds, hero tints):
```css
linear-gradient(135deg, rgba(124,58,237,0.1), rgba(124,58,237,0.05))
```

### Semantic / Status

| Role | Color |
|---|---|
| Success | `#10b981` |
| Warning | `#f59e0b` |
| Danger | `#ef4444` |
| Info | `#3b82f6` |

### Surface & Neutral Scale

**Light mode**
```css
--surface-bg:       #f3f4f6
--surface-card:     #ffffff
--admin-bg:         #f8f9fa
--admin-card-bg:    #ffffff
--admin-border:     #d1d5db
--text-main:        #111827
--text-muted:       #374151
--admin-text-muted: #9ca3af
```

**Dark mode** (`[data-bs-theme="dark"]`)
```css
--surface-bg:       #0f172a
--surface-card:     #1e293b
--admin-bg:         #0f172a
--admin-card-bg:    #1e293b
--admin-border:     #334155
--text-main:        #f1f5f9
--text-muted:       #c4cad4
```

### Glass Morphism (modals, floating cards)
```css
background: rgba(255,255,255,0.8);   /* light */
background: rgba(30,41,59,0.8);      /* dark */
border: 1px solid rgba(124,58,237,0.1); /* light border */
backdrop-filter: blur(10px);
```

---

## 2. School / Tenant Palette (Default Values)

These are the storage defaults in `SchoolInfo`; actual values come from the database at runtime.

| Field | Default | Meaning |
|---|---|---|
| `primary_color` | `#026e56` | Deep teal — main CTA, headings, nav active state |
| `secondary_color` | `#0f3b57` | Dark navy — sidebar, footer, dark sections |

Always reference these via CSS variables `var(--primary-color)` / `var(--secondary-color)` in school-facing templates, never hardcoded, so tenants can retheme.

Legacy gradient (classic/default landing hero):
```css
linear-gradient(135deg, #0f3b57 0%, #026e56 100%)
```

---

## 3. Typography

### App-Wide Body Font

**Manrope** — the single font used across all internal app pages (dashboard, admin panels, settings).

```html
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```

```css
font-family: 'Manrope', system-ui, sans-serif;
```

Weight usage:
- `400` — body text
- `500` — labels, secondary headings
- `600` — card titles, nav items
- `700` — page headings
- `800` — hero statements, stat numbers

### Landing Template Font Pairings

Each landing page template has its own curated type pairing. Match the pairing to the template:

| Template | Display / Heading | Body |
|---|---|---|
| **Japandi** | `Cormorant Garamond` (serif, 300–500) | `Inter` |
| **Art Deco** | `Cinzel` (display caps) + `Playfair Display` (subheadings) | `Cormorant Garamond` |
| **Elegant** | `Segoe UI` / system-ui | system-ui |
| **Classic / Modern / Minimal / Playful / Default** | Manrope (app default) | Manrope |

---

## 4. Shadow & Border Radius Tokens

```css
/* Radius */
--admin-radius-sm: 6px
--admin-radius-md: 8px
--admin-radius-lg: 12px
--card-radius:     16px   /* default card corners */

/* Shadow scale */
--admin-shadow-sm: 0 1px 2px rgba(0,0,0,0.05)
--admin-shadow-md: 0 4px 6px rgba(0,0,0,0.1)
--admin-shadow-lg: 0 10px 15px rgba(0,0,0,0.1)
--admin-shadow-xl: 0 20px 25px rgba(0,0,0,0.1)
--card-shadow:     0 10px 15px -3px rgba(0,0,0,0.05), 0 4px 6px -2px rgba(0,0,0,0.025)

/* Gold glow (use only in Elegant / Art Deco contexts) */
box-shadow: 0 10px 25px rgba(201,169,97,0.3)
```

---

## 5. Motion & Animation Tokens

SchoolPadi uses a single signature loader pattern — a running-light shimmer bar — not spinning circles.

```css
/* Top-edge navigation progress bar */
background: linear-gradient(
  90deg,
  transparent          0%,
  rgba(67,97,238,.55) 25%,
  #4361ee              50%,
  rgba(76,201,240,.9) 72%,
  transparent          100%
);
animation: padiExpressiveShimmer 1.6s cubic-bezier(0.37, 0, 0.63, 1) infinite;
```

Skeleton loaders:
```css
--skeleton-overlay-low: rgba(148,163,184,0.14)
--skeleton-overlay-mid: rgba(203,213,225,0.48)
--skeleton-duration:    1.15s
```

Dot pulse (loading cards):
```css
animation: padiDotPulse 1.2s ease-in-out infinite;
/* delay: 0s, 0.2s, 0.4s for three dots */
```

General motion principles:
- Page transitions: `0.2s–0.45s ease` (never abrupt, never sluggish)
- Hover lifts: `transform: translateY(-2px)` + shadow upgrade
- Staggered reveals: `animation-delay` increments of `0.1s–0.15s`
- Japandi templates only: use `1s–1.8s` slow fades (`cubic-bezier(0.25,0,0.1,1)`) for an ink-on-paper feel

---

## 6. Landing Template Palettes (quick reference)

### Japandi
```css
--washi: #F9F7F2  --linen: #EDE8DF  --stone: #D5CFC6
--moss:  #395440  --clay:  #A0714F  --ink:   #1C1C1C
```

### Art Deco
```css
--void:  #030608  --navy:  #07101E  --gold:  #C9A84C
--gold-lt:#E8C96A --ivory: #F5F0E8  --sapphire:#0F2D9A
```

### Elegant
```css
--elegant-navy: #1a2332  --elegant-gold: #c9a961
--elegant-charcoal: #2d3748
```

---

## 7. Rules When Applying This Brand

1. **Never hardcode school colors** in templates — always use `var(--primary-color)` / `var(--secondary-color)`.
2. **Admin chrome uses violet** (`#7c3aed`) not the school's primary color.
3. **Dark mode is mandatory** — every new component must define `[data-bs-theme="dark"]` overrides.
4. **Font on internal pages = Manrope only**. Landing pages may use their template-specific pairing.
5. **The loader bar is SchoolPadi's signature motion** — do not use spinner circles on page transitions.
6. **Japandi tone = calm and slow** — use long easing curves and generous whitespace.
7. **Art Deco tone = sharp and ceremonial** — high contrast gold on near-black, tight grid lines.
8. **Buttons**: primary CTA uses the `linear-gradient(135deg, #4361ee, #4cc9f0)` gradient with `border-radius: 10px–12px` and `font-weight: 600–700`.
