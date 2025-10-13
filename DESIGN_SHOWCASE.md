# 🎨 AMI - Design Showcase

## ✨ Modern, Beautiful, Professional

AMI non è solo un monitor di connessione - è un'**esperienza visiva** moderna e accattivante.

---

## 🌟 Splash Screen

All'avvio, AMI ti accoglie con uno **splash screen elegante**:

### Caratteristiche
- **Dark Theme** moderno con gradient blu scuro
- **Icona WiFi stilizzata** con archi animati
- **Typography pulita** con font system nativi
- **Fade-in/out** animazioni fluide
- **Progress messages** durante il caricamento

### Branding
```
Developed by CiaoIM™ by Daniel Giovannetti
Version 1.0.0 • 2025
```

### Colori
- Background: Gradient `#14172a → #243b55 → #14172a`
- Accent: Emerald Green `#34d399`
- Text: Slate `#e2e8f0`, `#94a3b8`

---

## 🎨 Dashboard - Dark Modern UI

La dashboard è stata **completamente ridisegnata** con un tema scuro professionale.

### 🌈 Palette Colori

| Elemento | Colore | Hex | Uso |
|----------|--------|-----|-----|
| **Online** | 🟢 Green | `#34d399` | Status positivo |
| **Unstable** | 🟡 Amber | `#fbbf24` | Warning |
| **Offline** | 🔴 Red | `#ef4444` | Errore |
| **Background** | 🌑 Dark | `#0f172a` | Sfondo principale |
| **Cards** | 🌑 Slate | `#1e293b` | Box e gruppi |
| **Text** | ⚪ Light | `#e2e8f0` | Testo primario |
| **Subtitle** | 🔵 Blue | `#94a3b8` | Testo secondario |

### 📐 Layout

```
┌──────────────────────────────────────────┐
│  🎯 Header                               │
│  • Titolo grande (24pt, bold, emerald)  │
│  • Tagline (11pt, italic, slate)        │
│  • Credit developer (8pt, gray)         │
├──────────────────────────────────────────┤
│  🌐 Current Status (GroupBox)           │
│  • 🟢 Status con icona                  │
│  • ⚡ Latency in tempo reale            │
│  • ✓ Success rate percentage            │
├──────────────────────────────────────────┤
│  📊 Statistics (GroupBox)               │
│  • 📈 Total Checks                      │
│  • ✅ Successful                        │
│  • ⏱️ Uptime %                          │
│  • 🕐 Duration                          │
├──────────────────────────────────────────┤
│  📉 Connection History (GroupBox)       │
│  • Graph 1: Status over time            │
│    - Scatter plot colorato              │
│    - Line plot con alpha                │
│  • Graph 2: Latency over time           │
│    - Line plot con fill gradient        │
├──────────────────────────────────────────┤
│  🎛️ Buttons                             │
│  • 🔄 Refresh Now                       │
│  • 🔄 Reset Statistics                  │
│  • ❌ Close                             │
└──────────────────────────────────────────┘
```

### 🎭 Elementi di Design

#### 1. **GroupBox Moderni**
```css
background: rgba(30, 41, 59, 0.6)
border: 2px solid #334155
border-radius: 10px
padding: 15px
```

#### 2. **Bottoni con Hover**
```css
Normal:  background #1e40af (blue)
Hover:   background #2563eb (lighter blue)
Pressed: background #1e3a8a (darker blue)
border-radius: 6px
padding: 8px 16px
```

#### 3. **Grafici Dark Theme**
- Background: `#0f172a` (dark slate)
- Grid: `#475569` (medium slate) con alpha 0.2
- Spines: `#475569`
- Labels: `#94a3b8` (light slate)
- Online dots: `#34d399` ✅
- Unstable dots: `#fbbf24` ⚠️
- Offline dots: `#ef4444` ❌

#### 4. **Icone Emoji**
- Status: 🟢 🟡 🔴
- Sections: 🌐 📊 📉
- Metrics: ⚡ ✓ 📈 ✅ ⏱️ 🕐
- Actions: 🔄 ❌

---

## 🎬 Animazioni & Transizioni

### Splash Screen
- **Fade In**: 800ms, EaseOutCubic
- **Fade Out**: 500ms, EaseInCubic
- **Auto-close**: Dopo 1.5 secondi

### Dashboard
- **Auto-refresh**: Ogni 5 secondi
- **Graph redraw**: Smooth transitions
- **Button hover**: Instant color change

---

## 💎 Details & Polish

### Typography
- **Headers**: Bold, grandi, emerald
- **Body**: Regular, readable, white/slate
- **Credits**: Small, discrete, gray

### Spacing
- **Margins**: 20px esterni
- **Spacing**: 15-25px tra elementi
- **Padding**: 15px nei box

### Borders
- **Radius**: 6-10px
- **Width**: 2-3px
- **Style**: Solid con colori subtili

### Shadows (simulated)
- Semi-transparent overlays
- Alpha blending per depth

---

## 🎯 User Experience

### All'Avvio
1. **Splash screen** appare centrato
2. **Loading messages** mostrano progress:
   - "Loading configuration..."
   - "Initializing network monitor..."
   - "Starting logger..."
   - "Preparing notifications..."
   - "Starting API server..."
   - "Finalizing..."
3. **Fade out** dopo completamento
4. **Dashboard** appare automaticamente (se configurato)

### Durante l'Uso
- **Icona tray** cambia colore (🟢🟡🔴)
- **Dashboard** aggiorna ogni 5s
- **Grafici** mostrano storia visivamente
- **Statistiche** in tempo reale

---

## 🔧 Personalizzazione

### Cambiare Colori

Modifica `src/dashboard.py`:

```python
# Colore accent principale
"#34d399"  # Emerald green

# Cambia in:
"#3b82f6"  # Blue
"#8b5cf6"  # Purple
"#f59e0b"  # Orange
```

### Cambiare Font

Modifica `src/splash_screen.py`:

```python
font = QFont("Montserrat", 48, QFont.Weight.Bold)
# Oppure
font = QFont("Roboto", 48, QFont.Weight.Bold)
```

### Cambiare Tema

Per un tema light, inverti i colori:
- Background: `#ffffff`
- Text: `#1e293b`
- Accents: Mantieni colorati

---

## 📸 Come Fare Screenshot

### macOS
```bash
# Avvia AMI
python AMI.py

# Splash screen: Cattura rapida (⌘⇧5)
# Dashboard: Aspetta apertura e cattura
```

### Windows
```bash
# Avvia AMI
AMI.exe

# Usa Win+Shift+S per catturare
```

---

## 🎨 Filosofia di Design

### Principi
1. **Dark First**: Tema scuro per ridurre affaticamento
2. **Color Meaningful**: Ogni colore ha significato
3. **Icon Rich**: Icone per riconoscibilità rapida
4. **Smooth**: Transizioni fluide, mai abrupte
5. **Professional**: Pulito, moderno, enterprise-ready

### Ispirazione
- **Tailwind CSS**: Palette colori
- **macOS Big Sur**: Rounded corners, translucency
- **Material Design**: Depth, shadows
- **Fluent Design**: Acrylic, modern buttons

---

## 🏆 Riconoscimenti

**Design & Development**
```
CiaoIM™ by Daniel Giovannetti
```

**Technologies**
- PyQt6 (Modern Qt framework)
- Matplotlib (Data visualization)
- Tailwind Colors (Modern palette)

---

## 📱 Future Enhancements

### Possibili Miglioramenti
- [ ] Blur effects (acrylic)
- [ ] Micro-animations (pulse su status change)
- [ ] Dark/Light theme toggle
- [ ] Custom theme picker
- [ ] Export theme JSON
- [ ] Graph interactions (zoom, pan)
- [ ] Sound effects (optional)
- [ ] System notifications integration

---

**"Beautiful design is functional design."**

© 2025 CiaoIM™ by Daniel Giovannetti
