# PDFSilo UI Colour System

This document defines the official colour palette and usage rules for the PDFSilo desktop interface.

PDFSilo is a privacy-focused local PDF processing application. Its visual identity should communicate:

- Trust and reliability
- Privacy and document security
- Technical precision
- Calm, efficient workflows
- Clear distinction between safe, destructive, warning, and informational actions

The palette is based on the PDFSilo logo: deep indigo/cobalt blue with a teal accent.

---

## 1. Brand colours

| Token | Hex | Purpose |
|---|---:|---|
| `brand-50` | `#EEF2FF` | Very light brand background |
| `brand-100` | `#E0E7FF` | Selected surfaces and subtle highlights |
| `brand-200` | `#C7D2FE` | Soft borders and decorative elements |
| `brand-300` | `#A5B4FC` | Secondary brand accents |
| `brand-400` | `#818CF8` | Hover accent on dark surfaces |
| `brand-500` | `#5B6EE1` | Main interactive blue |
| `brand-600` | `#4353C7` | Primary buttons and active controls |
| `brand-700` | `#3342A5` | Pressed states and strong emphasis |
| `brand-800` | `#27347F` | Dark brand surfaces |
| `brand-900` | `#1B2559` | Deep navy branding |
| `brand-950` | `#111936` | Darkest brand background |

### Teal accent

| Token | Hex | Purpose |
|---|---:|---|
| `accent-50` | `#ECFEFC` | Success-like accent background |
| `accent-100` | `#CFFAF6` | Soft teal selection |
| `accent-200` | `#9AF2EB` | Decorative accent |
| `accent-300` | `#5DE5DC` | Progress and active indicators |
| `accent-400` | `#2DD4C7` | Main logo accent |
| `accent-500` | `#16B8AE` | Teal button or focus accent |
| `accent-600` | `#0E918A` | Pressed teal |
| `accent-700` | `#0D716D` | Strong teal text |
| `accent-800` | `#105A58` | Dark teal surface |
| `accent-900` | `#124A49` | Deep teal |
| `accent-950` | `#052D2D` | Darkest teal |

### Core brand recommendation

Use these values most often:

```text
Primary brand:     #4353C7
Primary hover:     #3342A5
Primary light:     #EEF2FF
Primary dark:      #1B2559
Teal accent:       #2DD4C7
Teal active:       #16B8AE
```

---

## 2. Light mode

### Backgrounds and surfaces

| Token | Hex | Usage |
|---|---:|---|
| `light-bg-app` | `#F7F8FC` | Main application background |
| `light-bg-sidebar` | `#F0F2F8` | Sidebar background |
| `light-bg-surface` | `#FFFFFF` | Cards, dialogs, panels |
| `light-bg-surface-alt` | `#F8FAFC` | Secondary surface |
| `light-bg-hover` | `#F1F3FF` | Neutral or brand hover |
| `light-bg-selected` | `#E8ECFF` | Selected navigation or list item |
| `light-bg-disabled` | `#EEF0F4` | Disabled components |
| `light-bg-overlay` | `#FFFFFFE6` | Modal overlays over content |

### Text

| Token | Hex | Usage |
|---|---:|---|
| `light-text-primary` | `#151A2D` | Main text |
| `light-text-secondary` | `#4D566B` | Supporting text |
| `light-text-muted` | `#747D91` | Captions, metadata |
| `light-text-disabled` | `#A3A9B7` | Disabled labels |
| `light-text-on-brand` | `#FFFFFF` | Text on primary buttons |
| `light-text-link` | `#3342A5` | Links |
| `light-text-accent` | `#0D716D` | Teal emphasis |

### Borders and dividers

| Token | Hex | Usage |
|---|---:|---|
| `light-border-default` | `#D9DDE7` | Standard border |
| `light-border-subtle` | `#E8EAF0` | Light divider |
| `light-border-strong` | `#B8BFCE` | Strong field border |
| `light-border-focus` | `#4353C7` | Keyboard and input focus |
| `light-border-selected` | `#818CF8` | Selected cards or list items |

### Brand and interaction

| Token | Hex | Usage |
|---|---:|---|
| `light-primary` | `#4353C7` | Primary button |
| `light-primary-hover` | `#3342A5` | Primary button hover |
| `light-primary-pressed` | `#27347F` | Primary button pressed |
| `light-primary-subtle` | `#EEF2FF` | Brand-tinted background |
| `light-primary-disabled` | `#B7BEE8` | Disabled primary button |
| `light-accent` | `#16B8AE` | Accent action or progress |
| `light-accent-hover` | `#0E918A` | Accent hover |
| `light-focus-ring` | `#818CF866` | Focus ring with transparency |

---

## 3. Dark mode

The dark theme should use deep navy rather than pure black. This preserves the identity of the logo and reduces visual harshness during long PDF workflows.

### Backgrounds and surfaces

| Token | Hex | Usage |
|---|---:|---|
| `dark-bg-app` | `#0D1224` | Main application background |
| `dark-bg-sidebar` | `#11182E` | Sidebar background |
| `dark-bg-surface` | `#171F38` | Cards, dialogs, panels |
| `dark-bg-surface-alt` | `#1D2744` | Raised or alternate surface |
| `dark-bg-hover` | `#232E50` | Hovered neutral item |
| `dark-bg-selected` | `#293665` | Selected navigation or list item |
| `dark-bg-disabled` | `#20283B` | Disabled components |
| `dark-bg-overlay` | `#080C18E6` | Modal overlay |

### Text

| Token | Hex | Usage |
|---|---:|---|
| `dark-text-primary` | `#F4F6FB` | Main text |
| `dark-text-secondary` | `#C1C7D6` | Supporting text |
| `dark-text-muted` | `#929AAF` | Captions, metadata |
| `dark-text-disabled` | `#666F85` | Disabled labels |
| `dark-text-on-brand` | `#FFFFFF` | Text on primary buttons |
| `dark-text-link` | `#A5B4FC` | Links |
| `dark-text-accent` | `#5DE5DC` | Teal emphasis |

### Borders and dividers

| Token | Hex | Usage |
|---|---:|---|
| `dark-border-default` | `#303A56` | Standard border |
| `dark-border-subtle` | `#252E47` | Light divider |
| `dark-border-strong` | `#46516F` | Strong field border |
| `dark-border-focus` | `#818CF8` | Keyboard and input focus |
| `dark-border-selected` | `#A5B4FC` | Selected cards or list items |

### Brand and interaction

| Token | Hex | Usage |
|---|---:|---|
| `dark-primary` | `#6879EA` | Primary button |
| `dark-primary-hover` | `#7F8DF0` | Primary button hover |
| `dark-primary-pressed` | `#5264D5` | Primary button pressed |
| `dark-primary-subtle` | `#202A55` | Brand-tinted background |
| `dark-primary-disabled` | `#3F486F` | Disabled primary button |
| `dark-accent` | `#2DD4C7` | Accent action or progress |
| `dark-accent-hover` | `#5DE5DC` | Accent hover |
| `dark-focus-ring` | `#A5B4FC66` | Focus ring with transparency |

---

## 4. Semantic colours

Semantic colours should be consistent in both themes. Background, border, and text shades must adapt to the current mode.

### Success

```text
Light background: #ECFDF3
Light border:     #86E5AA
Light text:       #187A3F
Dark background:  #123523
Dark border:      #2D8A52
Dark text:        #76E39C
Solid action:     #218A4A
```

Use for:

- Successful operation completion
- Valid input paths
- Output successfully written
- Completed progress

### Warning

```text
Light background: #FFF8E5
Light border:     #F4CE73
Light text:       #855B00
Dark background:  #3A2C0D
Dark border:      #A87918
Dark text:        #FFD36A
Solid action:     #C48713
```

Use for:

- Large output size
- Existing file replacement warnings
- Partial compatibility warnings
- Non-blocking validation concerns

### Error and destructive action

```text
Light background: #FFF0F1
Light border:     #F3A2AA
Light text:       #A52432
Dark background:  #3D171D
Dark border:      #B24754
Dark text:        #FF9AA5
Solid action:     #C83C4A
Hover action:     #A92D3A
```

Use for:

- Failed operations
- Invalid input
- Delete, clear, remove, or overwrite actions
- Password and encryption errors

Red must not be used as a general PDF brand colour. Reserve it for error and destructive meaning.

### Information

```text
Light background: #EEF6FF
Light border:     #91C5F9
Light text:       #235F9D
Dark background:  #142D48
Dark border:      #397DB9
Dark text:        #86C7FF
Solid action:     #347FBE
```

Use for:

- Help messages
- Informational banners
- PDF metadata
- Neutral processing status

---

## 5. Component colour rules

### Primary button

Light mode:

```text
Background: #4353C7
Hover:      #3342A5
Pressed:    #27347F
Text:       #FFFFFF
Focus ring: #818CF866
```

Dark mode:

```text
Background: #6879EA
Hover:      #7F8DF0
Pressed:    #5264D5
Text:       #FFFFFF
Focus ring: #A5B4FC66
```

Use for one main action per view, such as:

- Merge
- Split
- Compress
- Encrypt
- Export
- Run operation

### Secondary button

Light mode:

```text
Background: #FFFFFF
Border:     #B8BFCE
Text:       #27347F
Hover:      #F1F3FF
```

Dark mode:

```text
Background: #1D2744
Border:     #46516F
Text:       #F4F6FB
Hover:      #293665
```

### Teal accent button

Use only for positive secondary actions, progress, or special privacy-related states.

Light mode:

```text
Background: #16B8AE
Hover:      #0E918A
Text:       #FFFFFF
```

Dark mode:

```text
Background: #2DD4C7
Hover:      #5DE5DC
Text:       #071D1C
```

### Destructive button

```text
Background: #C83C4A
Hover:      #A92D3A
Text:       #FFFFFF
```

Examples:

- Delete pages
- Clear all files
- Replace an existing output
- Remove selected item

### Input fields

Light mode:

```text
Background: #FFFFFF
Border:     #D9DDE7
Text:       #151A2D
Placeholder:#8C94A6
Hover:      #B8BFCE
Focus:      #4353C7
Invalid:    #C83C4A
Disabled:   #EEF0F4
```

Dark mode:

```text
Background: #171F38
Border:     #303A56
Text:       #F4F6FB
Placeholder:#778198
Hover:      #46516F
Focus:      #818CF8
Invalid:    #FF6F7B
Disabled:   #20283B
```

### Sidebar navigation

Light mode:

```text
Sidebar background: #F0F2F8
Item text:           #4D566B
Hover background:    #E9ECF7
Selected background: #E0E7FF
Selected text:       #27347F
Selected indicator:  #4353C7
```

Dark mode:

```text
Sidebar background: #11182E
Item text:           #C1C7D6
Hover background:    #1D2744
Selected background: #293665
Selected text:       #FFFFFF
Selected indicator:  #2DD4C7
```

### Progress bar

Light mode:

```text
Track: #E1E5ED
Fill:  #4353C7
Complete fill: #16B8AE
```

Dark mode:

```text
Track: #252E47
Fill:  #6879EA
Complete fill: #2DD4C7
```

### Cards and operation panels

Light mode:

```text
Background: #FFFFFF
Border:     #E2E5EC
Shadow:     rgba(20, 28, 55, 0.08)
```

Dark mode:

```text
Background: #171F38
Border:     #303A56
Shadow:     rgba(0, 0, 0, 0.28)
```

Avoid heavy glows in the product UI. The logo may use a subtle glow in promotional graphics, but the desktop application should remain flat, calm, and functional.

---

## 6. PDF-specific visual states

Use small colour accents to distinguish operation categories without recolouring the entire interface.

| Category | Colour | Example operations |
|---|---:|---|
| Organise | `#6879EA` | Merge, split, reorder, extract pages |
| Transform | `#16B8AE` | Rotate, render, images to PDF |
| Optimise | `#347FBE` | Compress |
| Protect | `#4353C7` | Encrypt, decrypt |
| Annotate | `#A05CC6` | Watermark, insert image |
| Destructive | `#C83C4A` | Delete pages, overwrite output |

These colours may be used for small icons, badges, or category indicators. Do not use them as full-page backgrounds.

---

## 7. Logo usage

### On light backgrounds

Use:

- Indigo wordmark: `#27347F` or `#3342A5`
- Indigo icon: `#3342A5`
- Teal lock/accent: `#2DD4C7`

Recommended background:

```text
#FFFFFF
#F7F8FC
#EEF2FF
```

### On dark backgrounds

Use:

- Light indigo wordmark: `#A5B4FC` or `#F4F6FB`
- Light indigo icon: `#818CF8`
- Teal lock/accent: `#5DE5DC`

Recommended background:

```text
#0D1224
#11182E
#171F38
```

### Monochrome logo

For one-colour printing or small interface placements:

```text
Light surfaces: #1B2559
Dark surfaces:  #FFFFFF
```

### Logo restrictions

Do not:

- Recolour the main logo red
- Apply a strong neon glow inside the application
- Place the dark logo on a dark background
- Use teal for the entire wordmark
- Add gradients to small app icons
- Use more than two brand colours in the primary logo
- Stretch or distort the logo
- Add an outline around the wordmark

---

## 8. Accessibility requirements

1. Normal text should meet at least WCAG AA contrast: `4.5:1`.
2. Large text and icons should meet at least `3:1`.
3. Do not rely on colour alone to communicate an error, warning, or success.
4. Pair semantic colours with icons and clear text.
5. All keyboard-focused controls must display a visible focus ring.
6. Disabled controls must remain readable but clearly inactive.
7. Teal text should only be used on sufficiently contrasting backgrounds.
8. Never place white text directly on `accent-300` without checking contrast.
9. Use red only with a textual or iconographic destructive cue.
10. Selected navigation must use colour plus an indicator bar or icon state.

---

## 9. PySide6 theme tokens

Suggested Python constants:

```python
# Brand
BRAND_50 = "#EEF2FF"
BRAND_100 = "#E0E7FF"
BRAND_300 = "#A5B4FC"
BRAND_400 = "#818CF8"
BRAND_500 = "#5B6EE1"
BRAND_600 = "#4353C7"
BRAND_700 = "#3342A5"
BRAND_800 = "#27347F"
BRAND_900 = "#1B2559"

ACCENT_300 = "#5DE5DC"
ACCENT_400 = "#2DD4C7"
ACCENT_500 = "#16B8AE"
ACCENT_600 = "#0E918A"

# Light theme
LIGHT_BG_APP = "#F7F8FC"
LIGHT_BG_SIDEBAR = "#F0F2F8"
LIGHT_BG_SURFACE = "#FFFFFF"
LIGHT_BG_SELECTED = "#E8ECFF"
LIGHT_TEXT_PRIMARY = "#151A2D"
LIGHT_TEXT_SECONDARY = "#4D566B"
LIGHT_TEXT_MUTED = "#747D91"
LIGHT_BORDER = "#D9DDE7"
LIGHT_PRIMARY = "#4353C7"
LIGHT_PRIMARY_HOVER = "#3342A5"
LIGHT_ACCENT = "#16B8AE"

# Dark theme
DARK_BG_APP = "#0D1224"
DARK_BG_SIDEBAR = "#11182E"
DARK_BG_SURFACE = "#171F38"
DARK_BG_SURFACE_ALT = "#1D2744"
DARK_BG_SELECTED = "#293665"
DARK_TEXT_PRIMARY = "#F4F6FB"
DARK_TEXT_SECONDARY = "#C1C7D6"
DARK_TEXT_MUTED = "#929AAF"
DARK_BORDER = "#303A56"
DARK_PRIMARY = "#6879EA"
DARK_PRIMARY_HOVER = "#7F8DF0"
DARK_ACCENT = "#2DD4C7"

# Semantic
SUCCESS = "#218A4A"
WARNING = "#C48713"
ERROR = "#C83C4A"
INFO = "#347FBE"
```

---

## 10. CSS-style token reference

```css
:root {
  --brand-primary: #4353C7;
  --brand-primary-hover: #3342A5;
  --brand-primary-pressed: #27347F;
  --brand-accent: #16B8AE;
  --brand-accent-bright: #2DD4C7;

  --bg-app: #F7F8FC;
  --bg-sidebar: #F0F2F8;
  --bg-surface: #FFFFFF;
  --bg-surface-alt: #F8FAFC;
  --bg-selected: #E8ECFF;

  --text-primary: #151A2D;
  --text-secondary: #4D566B;
  --text-muted: #747D91;

  --border-default: #D9DDE7;
  --border-focus: #4353C7;

  --success: #218A4A;
  --warning: #C48713;
  --error: #C83C4A;
  --info: #347FBE;
}

[data-theme="dark"] {
  --brand-primary: #6879EA;
  --brand-primary-hover: #7F8DF0;
  --brand-primary-pressed: #5264D5;
  --brand-accent: #2DD4C7;
  --brand-accent-bright: #5DE5DC;

  --bg-app: #0D1224;
  --bg-sidebar: #11182E;
  --bg-surface: #171F38;
  --bg-surface-alt: #1D2744;
  --bg-selected: #293665;

  --text-primary: #F4F6FB;
  --text-secondary: #C1C7D6;
  --text-muted: #929AAF;

  --border-default: #303A56;
  --border-focus: #818CF8;

  --success: #76E39C;
  --warning: #FFD36A;
  --error: #FF9AA5;
  --info: #86C7FF;
}
```

---

## 11. Final design direction

PDFSilo should look like a trustworthy desktop utility rather than a generic cybersecurity dashboard.

The visual balance should be:

```text
70% neutral backgrounds and surfaces
20% indigo brand colour
7% teal accent
3% semantic colours
```

Use indigo for primary actions and navigation. Use teal for progress, privacy accents, successful completion, and small highlights. Keep red exclusive to errors and destructive actions.
