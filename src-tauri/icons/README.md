# CNL Application Icons

## Required Icons

This directory needs the following icon files:

1. **32x32.png** - 32x32 pixel PNG icon
2. **128x128.png** - 128x128 pixel PNG icon
3. **128x128@2x.png** - 256x256 pixel PNG icon (2x retina)
4. **icon.icns** - macOS icon file (multi-resolution)
5. **icon.ico** - Windows icon file (multi-resolution)
6. **tray-icon.png** - System tray icon (16x16 and 32x32 recommended)
7. **tray-icon@2x.png** - Retina system tray icon (32x32)

## Placeholder Status

Currently using placeholder icons. Replace with actual Cisco/CNL branded icons for production.

## Icon Design Guidelines

- Use Cisco brand colors (blue: #049FD9)
- Consider incorporating:
  - Network/connectivity symbols
  - Neural/AI elements
  - Cisco logo elements
- Ensure good visibility at small sizes (16x16, 32x32)
- Test on both light and dark backgrounds

## Generating Icons

To generate all required formats from a single source:

```bash
# Option 1: Using ImageMagick
convert source.png -resize 32x32 32x32.png
convert source.png -resize 128x128 128x128.png
convert source.png -resize 256x256 128x128@2x.png
convert source.png -resize 16x16 tray-icon.png
convert source.png -resize 32x32 tray-icon@2x.png

# Option 2: Using online tools
# - https://www.img2go.com/convert-to-ico
# - https://cloudconvert.com/png-to-icns
```

## System Tray Icon Specifics

**macOS:**
- Use template images (monochrome) for proper light/dark mode support
- Recommended size: 16x16 at 1x, 32x32 at 2x
- Name format: `tray-iconTemplate.png` (macOS will auto-detect template mode)

**Windows:**
- Use colored icons
- Recommended size: 16x16 at 1x, 32x32 at 2x

**Linux:**
- Use colored or monochrome icons
- Recommended size: 16x16 at 1x, 32x32 at 2x

## Notes

- Icons must be square
- Use transparent backgrounds where appropriate
- PNG icons should be 32-bit RGBA
- ICNS and ICO files should contain multiple resolutions
