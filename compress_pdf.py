import img2pdf
from pdf2image import convert_from_path
from PIL import Image

def compress_pdf_to_target(
    input_pdf,
    output_pdf,
    target_bytes=1_000_000,
    poppler_path="./poppler",
    start_dpi=200,
    min_dpi=70,
    start_quality=85,
    min_quality=30,
):
    """
    Convert pages to JPEG images, rebuild PDF, and iteratively lower quality/dpi
    until file size <= target_bytes or minimums reached.
    Adapted for Appwrite: no os/tempfile, uses /tmp directory.
    """
    # default poppler path if not provided
    if poppler_path is None:
        poppler_path = "./poppler"  # include poppler binaries in your project

    dpi = start_dpi
    quality = start_quality

    # Read PDF content to memory to avoid os.path.getsize
    with open(input_pdf, "rb") as f:
        pdf_bytes = f.read()
    if len(pdf_bytes) <= target_bytes:
        return True

    while True:
        images = convert_from_path(input_pdf, dpi=dpi, poppler_path=poppler_path)
        jpg_paths = []

        # Save images to /tmp
        for i, img in enumerate(images):
            img = img.convert("RGB")
            max_width = 1600
            if img.width > max_width:
                h = int(max_width * img.height / img.width)
                img = img.resize((max_width, h), Image.LANCZOS)

            p = f"/tmp/page_{i+1}.jpg"
            img.save(p, "JPEG", quality=quality, optimize=True)
            jpg_paths.append(p)
            img.close()  # free memory

        # Build PDF
        with open(output_pdf, "wb") as f:
            f.write(img2pdf.convert(jpg_paths))

        # Check PDF size
        output_size = 0
        with open(output_pdf, "rb") as f:
            output_size = len(f.read())

        if output_size <= target_bytes:
            return True

        # Reduce quality first, then DPI
        if quality - 5 >= min_quality:
            quality -= 5
        elif dpi - 20 >= min_dpi:
            dpi -= 20
            quality = start_quality  # reset quality for new dpi
        else:
            return False
