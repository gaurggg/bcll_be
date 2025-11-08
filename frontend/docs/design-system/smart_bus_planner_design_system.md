# SMART BUS PLANNER – DESIGN SYSTEM v1.0

**Brand Essence:**  
Smart, Civic, Optimized, Accessible, Calm  
**Audience:** City Transport Officials, Urban Planners, Commuters (30–45 age group)

This design system ensures consistent, scalable design across all Smart Bus Planner experiences including web, mobile, dashboards, and public-facing interfaces.

---

## 1. BRAND IDENTITY

### 1.1 Core Themes
| Trait | Description | Visual Expression |
|------|-------------|------------------|
| Smart Efficiency | AI-powered optimization & clarity | Clean layouts, minimal decoration, precise spacing |
| Civic Trust | Public service & responsibility | Calm color palette, no harsh neons, stable shapes |
| Calm Confidence | Reduces complexity, encourages clarity | Smooth interactions, predictable UI behavior |
| Accessibility & Inclusiveness | Designed for every citizen | WCAG contrast, readable font sizes, clear labels |

---

## 2. COLOR SYSTEM

### 2.1 Primary Palette
| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Primary Blue | `#1A4D8F` | (26, 77, 143) | Brand identity, app bar, key text emphasis |
| Highlight Mint (CTA) | `#53C2A5` | (83, 194, 165) | Primary buttons, confirmations, highlighted states |
| Warm Neutral Sand | `#F5EEE3` | (245, 238, 227) | UI backgrounds, panels, surfaces |
| Graphite Gray | `#2B2B2B` | (43, 43, 43) | Headlines, critical labels, structured UI areas |
| Cool Slate | `#6B7A8F` | (107, 122, 143) | Secondary text, subtitles, metadata |

### 2.2 Status/Feedback Colors
| Name | Hex | Usage Rule |
|------|----|------------|
| Success | `#4CAF50` | Use for positive confirmations (Never for CTA) |
| Warning | `#FFC447` | Use for delays, peak loads, or pending changes |
| Error | `#E05A5A` | Use only for critical blocking issues |

### 2.3 Contrast & Accessibility
- Minimum text contrast ratio: **4.5:1**
- Never place light mint text on white or sand.
- Text on primary blue should be **white only**.

**Do:** Use Mint only for CTAs and highlights  
**Don’t:** Use Mint for titles, icons, or long text blocks

---

## 3. TYPOGRAPHY SYSTEM

### Font Families
| Usage | Font | Fallback |
|-------|------|----------|
| Primary UI & Body | Inter | system-ui, sans-serif |
| Branding, Titles | Manrope Semi-Bold | system-ui, sans-serif |
| Data Labels / Optional | Space Grotesk | system-ui, sans-serif |

### Type Scale
| Token | Size | Weight | Usage |
|-------|------|--------|-------|
| H1 | 36px | 600 | Page titles, hero headers |
| H2 | 28px | 600 | Section titles |
| H3 | 22px | 500 | Subsection labels |
| Body Large | 18px | 400 | Explanatory text |
| Body Default | 16px | 400 | Standard paragraphs |
| Body Small | 14px | 400 | Captions, secondary metadata |
| Data Label | 12–14px | 500 | Metrics, route names, node labels |

### Line Heights
- Headlines: 1.15
- Body text: 1.4
- Data labels: 1.25

**Do:** Keep text left-aligned for all UI  
**Don’t:** Center-align long body text or metric tables

---

## 4. SPACING & GRID

### 4.1 Spacing Tokens
| Token | Value |
|------|-------|
| XS | 4px |
| S | 8px |
| M | 12px |
| L | 16px |
| XL | 24px |
| XXL | 32px |

**Rule:** Use multiples of 4 only.

### 4.2 Layout Grid
| Device | Columns | Margin | Gutter |
|--------|---------|--------|--------|
| Desktop | 12 | 80–120px | 24px |
| Tablet | 8 | 24px | 16px |
| Mobile | 4 | 16px | 12px |

### 4.3 Card & Panel Padding
- Internal padding: 24px
- Vertical spacing: 16px

---

## 5. COMPONENT GUIDELINES

### 5.1 Buttons
| Type | Style | Usage |
|------|-------|-------|
| Primary | Background: `#53C2A5`, Text: White | Key actions |
| Secondary | Outline: `#1A4D8F`, Text: Primary Blue | Supporting actions |
| Tertiary | Text link | Low emphasis actions |

- Corner radius: 8px
- Hover: slightly darker shade + 1.02 scale
- Disabled: 30% opacity, no hover

**Do:** Only one Primary CTA per screen  
**Don’t:** Place two Primary buttons next to each other

### 5.2 Cards
- Background: White or Sand
- Radius: 8px
- Shadow: rgba(0,0,0,0.05) 0px 2px 6px

### 5.3 Navigation
- Top App Bar: 64px height
- Dashboard Left Menu: persistent
- Active item background: Primary Blue @ 12% opacity

### Iconography
- Style: 2px stroke outline icons
- Avoid playful or cartoon icons

---

## 6. MAP & DATA VISUALIZATION

- Route colors must be medium-saturation, non-neon
- Heatmap transitions must be smooth (>=1.5s fade)
- Label minimum size: 14px
- Avoid rotated text where possible

---

## 7. MOTION GUIDELINES

- Easing: cubic-bezier(0.4, 0.0, 0.2, 1)
- Interaction animations: 150–240ms
- Map transitions: 350–600ms
- No bouncy or elastic animations

---

## 8. BRAND DO’S AND DON’TS

| Do | Don’t |
|----|--------|
| Use calm, structured layouts | Add bright, saturated accents beyond mint |
| Prioritize accessibility & clarity | Use tiny text |
| Use visuals implying networks & connectivity | Use cartoon-style imagery |
| Keep spacing consistent | Allow crowded interfaces |

---

**End of Documentation**
