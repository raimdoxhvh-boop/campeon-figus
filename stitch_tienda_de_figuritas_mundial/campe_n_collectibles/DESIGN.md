---
name: Campeón Collectibles
colors:
  surface: '#f9f9ff'
  surface-dim: '#d8d9e4'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3fe'
  surface-container: '#ecedf8'
  surface-container-high: '#e6e8f2'
  surface-container-highest: '#e0e2ed'
  on-surface: '#181b23'
  on-surface-variant: '#3d4a3f'
  inverse-surface: '#2d3038'
  inverse-on-surface: '#eff0fb'
  outline: '#6d7a6e'
  outline-variant: '#bccabc'
  surface-tint: '#006d37'
  primary: '#006d37'
  on-primary: '#ffffff'
  primary-container: '#27ae60'
  on-primary-container: '#00391a'
  inverse-primary: '#61de8a'
  secondary: '#735c00'
  on-secondary: '#ffffff'
  secondary-container: '#fed023'
  on-secondary-container: '#6f5900'
  tertiary: '#c00001'
  on-tertiary: '#ffffff'
  tertiary-container: '#ff6753'
  on-tertiary-container: '#690000'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#7efba4'
  primary-fixed-dim: '#61de8a'
  on-primary-fixed: '#00210c'
  on-primary-fixed-variant: '#005228'
  secondary-fixed: '#ffe084'
  secondary-fixed-dim: '#eec209'
  on-secondary-fixed: '#231b00'
  on-secondary-fixed-variant: '#574500'
  tertiary-fixed: '#ffdad4'
  tertiary-fixed-dim: '#ffb4a8'
  on-tertiary-fixed: '#410000'
  on-tertiary-fixed-variant: '#930001'
  background: '#f9f9ff'
  on-background: '#181b23'
  surface-variant: '#e0e2ed'
  pitch-green: '#0D6B48'
  trophy-gold: '#FFF200'
  action-orange: '#E67E22'
  clean-white: '#FFFFFF'
typography:
  headline-xl:
    fontFamily: Lexend
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Lexend
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Lexend
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-md:
    fontFamily: Lexend
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  body-lg:
    fontFamily: Source Sans 3
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Source Sans 3
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-bold:
    fontFamily: Lexend
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  price-display:
    fontFamily: Lexend
    fontSize: 24px
    fontWeight: '800'
    lineHeight: 24px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 64px
  max-width: 1280px
---

## Brand & Style

The design system is built to capture the electric atmosphere of the World Cup and the nostalgic thrill of sticker collecting. The brand personality is **vibrant, energetic, and celebratory**, targeting fans who value speed, authenticity, and the "chase" of completing an album.

The visual style is **High-Contrast / Bold**, utilizing saturation and sharp typography to drive action. It draws from the aesthetic of sports broadcasting and stadium graphics: heavy shadows, thick borders, and high-impact color blocking. The UI should feel like a premium sports card—tactile, valuable, and dynamic. Every interaction should reinforce the excitement of the "unboxing" or "trading" experience.

## Colors

The palette is rooted in the "Pitch Green" and "Trophy Gold" of the football world. **Primary Green** (#27AE60) is used for main brand elements and success states, symbolizing the field of play. **Secondary Gold** (#F1C40F) is the primary accent for CTA buttons and "Golden Sticker" highlights, creating a sense of value and achievement.

**Tertiary Red** (#D20303) is reserved for urgency, discounts, and "limited stock" alerts to drive immediate conversions. The **Neutral** (#282B33) is a deep charcoal rather than pure black, providing a high-contrast foundation for text and containers that feels modern and sporty.

## Typography

This design system uses **Lexend** for all headlines and labels. Its geometric clarity and varied weights provide the athletic, high-energy look required for a sports store. Headlines should be set with tight letter spacing and heavy weights (700-800) to mimic stadium scoreboard aesthetics.

For body text, **Source Sans 3** provides a neutral, highly legible contrast that ensures product descriptions and checkout details remain clear and functional. Prices should always be rendered in Lexend Bold to emphasize the commercial aspect of the collectible market.

## Layout & Spacing

The layout follows a **Fixed Grid** model on desktop to maintain the "Collector's Album" feel, while transitioning to a fluid single or double-column stack on mobile. 

- **Grid:** 12-column system for desktop, 4-column for mobile.
- **Product Grids:** Stickers and packs are displayed in a rigid 2, 3, or 4-column grid with consistent 16px gutters to resemble the slots in a sticker album.
- **Rhythm:** A 4px baseline grid ensures tight, organized spacing between related elements (e.g., price and product name).
- **Checkout Flow:** Uses a centered, narrowed layout (600px max) to minimize distractions and lead the user directly through the payment funnel.

## Elevation & Depth

Visual hierarchy is achieved through **Tonal Layers** and **Bold Borders**. Surfaces are rarely "flat"; they use subtle gradients or high-contrast strokes to stand out.

- **Level 1 (Cards):** 1px solid border (#282B33 at 10% opacity) with no shadow.
- **Level 2 (Hover/Active):** A hard, "sticker-peel" shadow (4px 4px 0px #282B33) to give the UI a physical, tactile quality.
- **Level 3 (Modals/Popups):** High-contrast dark overlays (80% opacity) with the modal surface using a "Pitch Green" tint to maintain brand immersion.
- **Depth Metaphor:** Elements should feel like they are layered on top of each other, similar to stickers being placed on a page.

## Shapes

The design system utilizes **Rounded** (Level 2) corners (0.5rem / 8px). This strikes a balance between the aggressive energy of sports and the friendly, approachable nature of a hobby store. 

- **Stickers/Products:** Use a slightly larger `rounded-lg` (1rem) to mimic the die-cut corners of physical stickers.
- **Input Fields:** Use standard 8px rounding for a professional, secure feel.
- **Buttons:** Use 8px rounding; avoid pill shapes to maintain the "card-like" structural integrity of the layout.

## Components

### Buttons
- **Primary:** Trophy Gold background, black text, bold Lexend. On hover, apply the hard 4px shadow for a tactile "pressed" effect.
- **Secondary:** Pitch Green background, white text.
- **Ghost:** Transparent with a 2px Pitch Green border.

### Product Cards
- Cards must have a clear white background with a subtle gray border. 
- The "Add to Cart" button should be permanently visible or appear on hover to facilitate quick, repetitive purchases (common for stickers).
- "Rare" or "Legendary" stickers should feature a shimmering Gold border effect.

### Chips & Tags
- Use tags for "In Stock," "Rare," or "Argentina Team." 
- Tags use high-contrast backgrounds (Red for "Sold Out," Green for "New") and all-caps Lexend labels.

### Inputs & Checkout
- Input fields use a thick 2px border on focus in Primary Green.
- The checkout progress bar uses "Sticker Icons" to represent steps (Cart -> Shipping -> Payment -> Success).

### Progress Indicators
- For "Album Progress," use a thick green bar with a percentage counter, motivating users to buy more to reach 100%.