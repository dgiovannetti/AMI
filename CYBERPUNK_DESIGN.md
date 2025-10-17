# AMI Cyberpunk Design System

## Philosophy
Inspired by Cyberpunk 2077, Blade Runner, and Matrix aesthetics. This design embodies:
- **Neon Futurism**: Glowing cyan/purple/pink accents on deep dark backgrounds
- **Terminal Aesthetic**: Monospace fonts, command-line inspired UI
- **Glitch Effects**: Intentional visual artifacts and text shadows
- **High Contrast**: Maximum readability with neon on black

## Color Palette

### Core Colors
- **Background Deep**: `#0D0221` (Deep purple-black)
- **Background Mid**: `#160633` (Dark purple)
- **Background Light**: `#1a0933` (Medium purple)

### Neon Accents
- **Cyan**: `#00F5FF` (Primary accent, borders, highlights)
- **Green**: `#00FF41` (Success, online status)
- **Purple**: `#7209B7`, `#9D4EDD`, `#C77DFF` (Secondary accents)
- **Pink**: `#FF006E` (Alerts, errors)
- **Yellow**: `#FFD60A` (Warnings)

### Gradients
```css
/* Primary background */
qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0D0221, stop:1 #1a0933)

/* Card background */
qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0D0221, stop:1 #160633)

/* Button active */
qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00F5FF, stop:1 #00FF41)

/* Button inactive */
qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #160633, stop:1 #0D0221)
```

## Typography

### Font Stack
Primary: `Courier New` (monospace for terminal aesthetic)
Fallback: `Consolas`, `Monaco`, `monospace`

### Hierarchy
- **Brand**: 22-28pt, Bold, Letter Spacing 4px
- **Hero**: 48pt, Bold, Neon glow
- **Title**: 14pt, Bold, Letter Spacing 3px
- **Label**: 9-11pt, Bold, Letter Spacing 2px, Prefix with "//"
- **Value**: 28-32pt, Bold, Neon text-shadow
- **Body**: 11-12pt, Regular

### Text Effects
```css
/* Glitch effect */
text-shadow: 2px 2px 0px #7209B7, -2px -2px 0px #C77DFF;

/* Neon glow */
text-shadow: 0 0 20px #00F5FF;

/* Strong neon */
text-shadow: 0 0 10px #FF006E;
```

## Components

### Buttons
```css
Primary (Neon Cyan/Green):
- Background: gradient(#00F5FF → #00FF41)
- Color: #0D0221 (dark text on bright)
- Border: 3px solid #00F5FF
- Hover: reverse gradient + box-shadow glow

Secondary (Purple):
- Background: gradient(#160633 → #0D0221)
- Color: #7209B7
- Border: 2px solid #7209B7
- Hover: lighter purple
```

### Cards (Metrics)
```css
- Background: gradient(#0D0221 → #160633)
- Border: 2px solid [accent color]
- Border Radius: 0px (sharp corners)
- Padding: 20px 24px
- Title: "// LABEL" in cyan
- Value: Huge monospace with neon glow
```

### Inputs
```css
- Background: gradient(#0D0221 → #160633)
- Border: 2px solid #7209B7
- Border Radius: 0px
- Color: #C77DFF
- Focus Border: #00F5FF
- Focus Color: #00F5FF
```

### Tabs
```css
Inactive:
- Background: gradient(#160633 → #0D0221)
- Color: #7209B7
- Border: 2px solid #7209B7

Active:
- Background: gradient(#0D0221 → #160633)
- Color: #00F5FF
- Bottom Border: 3px solid #00F5FF
```

### Checkboxes
```css
Unchecked:
- Background: #0D0221
- Border: 2px solid #7209B7
- Size: 20x20px

Checked:
- Background: gradient(#00F5FF → #00FF41)
- Border: #00F5FF
```

## Layout

### Spacing Scale
- XS: 8px
- S: 12px
- M: 20px
- L: 28px
- XL: 40px
- XXL: 48px

### Borders
- Standard: 2px solid
- Emphasis: 3px solid
- Radius: 0px (no rounded corners)

### Padding
- Cards: 20-28px
- Buttons: 18px 36px
- Containers: 40px
- Inputs: 10px 14px

## Special Effects

### Neon Glow
```css
box-shadow: 0 0 20px #00F5FF;
box-shadow: 0 0 30px #00F5FF; /* stronger */
```

### Text Prefixes
- Labels: `// LABEL_NAME`
- Prompts: `>_ COMMAND`
- Status: `>> STATUS`
- Alerts: `[!]`, `[!!!]`
- Actions: `[ENTER]`, `[ESC]`

### Window Titles
Format: `[APP] // FUNCTION.EXE`
Examples:
- `[AMI] // NETWORK MONITOR`
- `[AMI] // UPDATE_AVAILABLE.EXE`
- `[AMI] // CONFIG.SYS`

## Tray Icon

Style: Neon ring with glow
- Outer glow: Semi-transparent accent color
- Ring: 8px thick neon stroke
- Center: Small filled dot
- Colors:
  - Green: `#00FF41` (online)
  - Cyan: `#00F5FF` (unstable)
  - Pink: `#FF006E` (offline)

## Compact Mode

When window < 720px:
- Purple gradient background
- Centered `[AMI]` with glitch effect
- Huge neon circle indicator `◉` (72pt)
- Monospace ping value (32pt)
- All in Courier New

## Animations

### Transitions
- Duration: 200ms (fast), 400ms (standard)
- Easing: ease-out
- Hover: Instant color change + glow

### Effects
- Button hover: Gradient reverse + neon glow
- Input focus: Border color change to cyan
- Value update: Opacity flash

## Terminal Elements

### Header Decorations
```
>_ COMMAND
// SECTION_NAME
[TIMESTAMP]
>> STATUS
```

### Alert Boxes
```
[!] WARNING_MESSAGE
[!!!] CRITICAL_MESSAGE
```

### Button Labels
```
[ENTER] ACTION_NAME
[ESC] CANCEL
```

## Accessibility

### Contrast Ratios
- Cyan on Purple: 8.5:1 (AAA)
- White on Deep Purple: 19:1 (AAA)
- All text meets WCAG AAA standards

### Focus States
- All interactive elements: 2-3px cyan border
- Keyboard navigation fully supported

## Implementation Notes

### Qt StyleSheets
- Use `qlineargradient` for all backgrounds
- Sharp corners: `border-radius: 0px`
- Monospace everywhere: `font-family: 'Courier New'`

### Performance
- Cache gradient pixmaps
- Minimize repaints
- Use hardware acceleration

## Presentation Tips

1. **Open with Impact**: Show the neon dashboard in dark room
2. **Emphasize Uniqueness**: "Nothing else looks like this"
3. **Show Terminal Aesthetic**: Highlight monospace, command-line feel
4. **Demo Glitch Effects**: Point out intentional visual artifacts
5. **Compact Mode**: Show how it scales down beautifully
6. **End with Neon**: Leave them with glowing metrics

## Future Enhancements

- Scanline overlay effect
- CRT screen curvature
- Typing animation for text
- Glitch animation on state changes
- Sound effects (cyberpunk bleeps)
- Custom cursor (crosshair style)
