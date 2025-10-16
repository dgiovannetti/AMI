# AMI Design System - Tesla/SpaceX Aesthetic

## Philosophy
Inspired by Tesla UI, SpaceX Mission Control, and X (Twitter), this design system embodies:
- **Radical Minimalism**: Zero unnecessary elements
- **Data First**: Large, bold metrics with instant readability
- **High Contrast**: Pure black backgrounds with bright accents
- **Functional Beauty**: Every pixel serves a purpose

## Color Palette

### Core Colors
- **Background**: `#000000` (Pure Black)
- **Surface**: `#0a0a0a`, `#1a1a1a` (Near Black)
- **Borders**: `#222222`, `#333333` (Subtle Gray)

### Accent Colors
- **Primary (Tesla Red)**: `#E82127`
  - Hover: `#ff3339`
  - Pressed: `#cc1a1f`
- **Success (Green)**: `#34d399`
- **Warning (Amber)**: `#fbbf24`
- **Error (Red)**: `#ef4444`
- **Info (Blue)**: `#60a5fa`

### Text Colors
- **Primary**: `#ffffff` (Pure White)
- **Secondary**: `#cccccc` (Light Gray)
- **Tertiary**: `#666666` (Medium Gray)
- **Disabled**: `#333333` (Dark Gray)

## Typography

### Font Stack
Primary: SF Pro Display (macOS), Segoe UI (Windows), system-ui

### Hierarchy
- **Hero**: 32pt, Bold, Letter Spacing 2px
- **Title**: 20pt, Bold, Letter Spacing 2px
- **Heading**: 18pt, Bold, Letter Spacing 1.5px
- **Subheading**: 11pt, Bold, Letter Spacing 1.5px
- **Body**: 13pt, Semi-Bold, Letter Spacing 0.5px
- **Caption**: 10pt, Regular, Letter Spacing 0.5px

### Uppercase Usage
- All buttons: UPPERCASE
- Section headers: UPPERCASE
- Labels: UPPERCASE with increased letter spacing

## Components

### Buttons
```css
Primary (Tesla Red):
- Background: #E82127
- Color: #ffffff
- Padding: 16px 32px
- Border Radius: 4px
- Font: 13pt Bold, Letter Spacing 1.5px

Secondary:
- Background: #0a0a0a
- Color: #ffffff
- Border: 1px solid #222222
- Same padding and typography as primary
```

### Cards (Metrics)
```css
- Background: #000000
- Border: 1px solid #1a1a1a
- Border Radius: 4px
- Padding: 16px 20px
- Title: 8pt Bold, #666666, Letter Spacing 1.5px
- Value: 32pt Bold, Accent Color
- Glow Effect: 20px blur on value
```

### Inputs
```css
- Background: #0a0a0a
- Border: 1px solid #222222
- Border Radius: 4px
- Padding: 8px 12px
- Focus Border: #E82127
- Color: #ffffff
```

### Tabs
```css
Inactive:
- Background: #0a0a0a
- Color: #666666
- Border: 1px solid #222222

Active:
- Background: #000000
- Color: #ffffff
- Bottom Border: 2px solid #E82127
```

## Layout

### Spacing Scale
- XS: 4px
- S: 8px
- M: 16px
- L: 24px
- XL: 32px
- XXL: 48px

### Grid
- Metrics: 4-column grid on desktop, responsive to 2 or 1 column
- Gap: 16px
- Container Padding: 32px

## Animations

### Transitions
- Duration: 200ms (fast), 400ms (standard)
- Easing: ease-out for entrances, ease-in for exits
- Hover states: instant color change, no delay

### Effects
- Glow on metric values: 20px blur, accent color
- Button hover: background lightens by 10%
- Focus: border color change to Tesla Red

## Icons

### Tray Icon
- Style: Simple filled circle
- Size: 64x64 (in 128x128 canvas for HiDPI)
- Colors: Match status (green/amber/red)
- No gradients or decorations

### UI Icons
- Minimal, line-based when possible
- Emoji for quick recognition (🔄, ⚙️, 📊)
- Size: 16-20px

## Compact Mode

When window < 720px width or < 420px height:
- Show only: Brand name, huge status indicator (●), ping value
- Center all elements
- Status indicator: 64pt
- Ping: 28pt
- Brand: 24pt with 3px letter spacing

## Accessibility

### Contrast Ratios
- White on Black: 21:1 (AAA)
- Tesla Red on Black: 7.2:1 (AA)
- All text meets WCAG AA standards

### Focus States
- All interactive elements have visible focus
- Focus indicator: 2px Tesla Red border

## Implementation Notes

### Qt StyleSheets
- Use QSS for consistent styling
- Define global styles in main window
- Override locally only when necessary

### Performance
- Minimize repaints with cached pixmaps
- Use hardware acceleration for animations
- Lazy load heavy components (charts)

## Presentation Tips for Elon

1. **Open with Impact**: Show the pure black dashboard with glowing metrics
2. **Emphasize Speed**: Demonstrate instant feedback and smooth transitions
3. **Highlight Minimalism**: "Every pixel has a purpose - no clutter"
4. **Show Compact Mode**: "Works beautifully even on small screens"
5. **Demo Update Flow**: Tesla Red button, clear messaging, no friction
6. **End with Metrics**: Show real-time data, emphasize clarity

## Future Enhancements

- Dark mode auto-switching based on time
- Customizable accent colors (keep Tesla Red as default)
- Animated status transitions
- Sound design (subtle, SpaceX-inspired)
- Gesture support for trackpad users
