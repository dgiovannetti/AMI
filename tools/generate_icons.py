"""
Icon Generator for AMI
Creates application icons in various formats and colors
"""

from PIL import Image, ImageDraw
import os


def create_wifi_icon(size=256, color=(0, 200, 0), bg_color=(255, 255, 255, 0)):
    """
    Create a Wi-Fi icon with check mark
    
    Args:
        size: Icon size in pixels
        color: RGB tuple for the icon color
        bg_color: RGBA tuple for background (transparent by default)
        
    Returns:
        PIL Image object
    """
    # Create image with transparency
    img = Image.new('RGBA', (size, size), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Calculate proportions
    center_x = size // 2
    center_y = size // 2
    
    # Draw Wi-Fi arcs (3 arcs)
    line_width = max(2, size // 32)
    
    # Inner arc
    arc1_box = [
        center_x - size * 0.15, center_y - size * 0.15,
        center_x + size * 0.15, center_y + size * 0.15
    ]
    draw.arc(arc1_box, start=200, end=340, fill=color, width=line_width)
    
    # Middle arc
    arc2_box = [
        center_x - size * 0.25, center_y - size * 0.25,
        center_x + size * 0.25, center_y + size * 0.25
    ]
    draw.arc(arc2_box, start=200, end=340, fill=color, width=line_width)
    
    # Outer arc
    arc3_box = [
        center_x - size * 0.35, center_y - size * 0.35,
        center_x + size * 0.35, center_y + size * 0.35
    ]
    draw.arc(arc3_box, start=200, end=340, fill=color, width=line_width)
    
    # Draw center dot
    dot_size = size // 12
    dot_box = [
        center_x - dot_size, center_y + size * 0.1,
        center_x + dot_size, center_y + size * 0.1 + dot_size * 2
    ]
    draw.ellipse(dot_box, fill=color)
    
    # Draw check mark in top-right corner
    check_size = size // 4
    check_x = size - check_size - size // 10
    check_y = size // 10
    
    # Check mark background circle
    check_bg_box = [
        check_x - check_size * 0.6, check_y - check_size * 0.2,
        check_x + check_size * 0.6, check_y + check_size * 1.0
    ]
    draw.ellipse(check_bg_box, fill=(255, 255, 255, 230))
    
    # Check mark itself
    check_points = [
        (check_x - check_size * 0.3, check_y + check_size * 0.3),
        (check_x - check_size * 0.1, check_y + check_size * 0.5),
        (check_x + check_size * 0.3, check_y + check_size * 0.1)
    ]
    draw.line(check_points, fill=(0, 150, 0), width=line_width * 2, joint="curve")
    
    return img


def create_simple_icon(size=256, color=(0, 200, 0)):
    """
    Create a simple circular status icon
    
    Args:
        size: Icon size in pixels
        color: RGB tuple for the icon color
        
    Returns:
        PIL Image object
    """
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw outer circle (border)
    margin = size // 8
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=color,
        outline=(255, 255, 255, 255),
        width=max(2, size // 64)
    )
    
    # Draw Wi-Fi symbol
    center_x = size // 2
    center_y = size // 2
    
    # Wi-Fi arcs
    line_width = max(2, size // 32)
    
    # Arc 1
    arc1_box = [
        center_x - size * 0.15, center_y - size * 0.08,
        center_x + size * 0.15, center_y + size * 0.18
    ]
    draw.arc(arc1_box, start=180, end=360, fill=(255, 255, 255), width=line_width)
    
    # Arc 2
    arc2_box = [
        center_x - size * 0.22, center_y - size * 0.12,
        center_x + size * 0.22, center_y + size * 0.25
    ]
    draw.arc(arc2_box, start=180, end=360, fill=(255, 255, 255), width=line_width)
    
    # Dot
    dot_size = size // 16
    dot_box = [
        center_x - dot_size, center_y + size * 0.12,
        center_x + dot_size, center_y + size * 0.12 + dot_size * 2
    ]
    draw.ellipse(dot_box, fill=(255, 255, 255))
    
    return img


def save_icon_set(output_dir='../resources'):
    """
    Generate and save complete icon set
    
    Args:
        output_dir: Directory to save icons
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    colors = {
        'green': (0, 200, 0),
        'yellow': (255, 200, 0),
        'red': (255, 0, 0)
    }
    
    sizes = [16, 24, 32, 48, 64, 128, 256]
    
    print("Generating AMI icons...")
    
    # Generate main icon with check mark
    print("  Creating main icon (ami.png)...")
    main_icon = create_wifi_icon(256, colors['green'])
    main_icon.save(os.path.join(output_dir, 'ami.png'))
    
    # Generate .ico file (Windows)
    print("  Creating Windows icon (ami.ico)...")
    icon_images = [create_wifi_icon(s, colors['green']) for s in [16, 32, 48, 64, 128, 256]]
    icon_images[0].save(
        os.path.join(output_dir, 'ami.ico'),
        format='ICO',
        sizes=[(s, s) for s in [16, 32, 48, 64, 128, 256]]
    )
    
    # Generate status icons (simple circular)
    for color_name, color_value in colors.items():
        print(f"  Creating {color_name} status icons...")
        
        # PNG
        icon = create_simple_icon(64, color_value)
        icon.save(os.path.join(output_dir, f'status_{color_name}.png'))
    
    # Generate logo for about dialog
    print("  Creating logo (ami_logo.png)...")
    logo = create_wifi_icon(512, colors['green'])
    logo.save(os.path.join(output_dir, 'ami_logo.png'))
    
    print(f"\n[OK] Icons generated successfully in '{output_dir}/'")
    print("  Files created:")
    print("    - ami.png (main icon)")
    print("    - ami.ico (Windows icon)")
    print("    - status_green.png")
    print("    - status_yellow.png")
    print("    - status_red.png")
    print("    - ami_logo.png")


if __name__ == '__main__':
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    resources_dir = os.path.join(script_dir, '..', 'resources')
    
    save_icon_set(resources_dir)
