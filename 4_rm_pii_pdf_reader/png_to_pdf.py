from PIL import Image
import os
import sys

def png_to_pdf(input_png):
    """Convert a PNG image to a PDF file with the same base name."""
    base, _ = os.path.splitext(input_png)
    output_pdf = base + ".pdf"
    image = Image.open(input_png)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(output_pdf, "PDF", resolution=100.0)
    print(f"Converted {input_png} to {output_pdf}")

if __name__ == "__main__":
    png_to_pdf('4_rm_pii_pdf_reader/Bob_Bild.png')
