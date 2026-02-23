"""
Generate QR codes for High Five Recognition tokens
Usage: python generate_qr_codes.py
"""

import qrcode
import qrcode.image.svg
import os
from typing import List

# Configuration
APP_URL = "https://highfive.streamlit.app/"
OUTPUT_DIR = "qr_codes"

# Recognition categories with hex codes
CATEGORY_COLORS = {
    "collaboration_excellence": "#9E2896",
    "knowledge_growth": "#007BC0",
    "supplier_management": "#18837E",
    "performance_delivery": "#00884A",
}

# List of category names
CATEGORIES = list(CATEGORY_COLORS.keys())


def generate_qr_code(
    token: str,
    category: str,
    output_path: str,
    format: str = "svg",
    qr_color: str = None,
):
    """Generate a QR code for a specific token and category"""
    url = f"{APP_URL}?token={token}&category={category}"

    # Use custom color or default to black
    fill_color = qr_color if qr_color else "black"

    if format == "svg":
        # Generate SVG (vector format) with color support
        factory = qrcode.image.svg.SvgFillImage
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
            image_factory=factory,
        )
        qr.add_data(url)
        qr.make(fit=True)
        # SvgFillImage uses different parameter names
        img = qr.make_image(fill=fill_color, back_color="white")
        img.save(output_path)
    else:
        # Generate PNG (raster format)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fill_color, back_color="white")
        img.save(output_path)

    print(f"✓ Generated: {output_path} (color: {fill_color})")


def generate_batch(
    prefix: str,
    start: int,
    count: int,
    categories: List[str],
    format: str = "svg",
    use_colored_qr: bool = True,
):
    """Generate a batch of QR codes"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    extension = "svg" if format == "svg" else "png"

    for i in range(start, start + count):
        token = f"{prefix}{i:03d}"  # e.g., CONF001, CONF002
        category = categories[i % len(categories)]  # Cycle through categories

        filename = f"{token}_{category}.{extension}"
        output_path = os.path.join(OUTPUT_DIR, filename)

        # Use the hex color for QR code if enabled
        qr_color = CATEGORY_COLORS.get(category) if use_colored_qr else None

        generate_qr_code(token, category, output_path, format, qr_color)


def main():
    print("🎨 High Five QR Code Generator\n")

    print("Examples:")
    print("  1. Conference tokens: CONF001-CONF100")
    print("  2. Team tokens: TEAM-A-001, TEAM-B-001")
    print("  3. Department tokens: HR-001, IT-001")
    print()

    # Get user input
    prefix = input("Enter token prefix (e.g., CONF, TEAM, EVENT): ").strip()
    start_num = int(input("Start number (e.g., 1): "))
    count = int(input("How many QR codes to generate: "))
    format_choice = input("Format (png/svg) [default: svg]: ").strip().lower() or "svg"

    # Ask if user wants colored QR codes (default: yes)
    colored_qr = (
        input(
            "Generate colored QR codes matching categories? (yes/no) [default: yes]: "
        )
        .strip()
        .lower()
    )
    use_colored_qr = colored_qr != "no"

    if use_colored_qr:
        print("\n🎨 Available categories:")
        for category_name, hex_code in CATEGORY_COLORS.items():
            print(f"  • {category_name}: {hex_code}")
        print()

    print(
        "\n⚠️  Make sure to update APP_URL in this script to your actual Streamlit app URL!"
    )
    print(f"Current URL: {APP_URL}\n")

    proceed = input("Generate QR codes? (yes/no): ").strip().lower()

    if proceed == "yes":
        qr_type = "colored" if use_colored_qr else "black"
        print(
            f"\n🚀 Generating {count} {qr_type} {format_choice.upper()} QR codes...\n"
        )
        generate_batch(
            prefix, start_num, count, CATEGORIES, format_choice, use_colored_qr
        )
        print(f"\n✅ Done! QR codes saved to '{OUTPUT_DIR}/' directory")
        print(
            "\n💡 Tip: You can now print these QR codes and attach them to physical tokens!"
        )
    else:
        print("Cancelled.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
