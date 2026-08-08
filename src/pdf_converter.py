import os
import shutil
import subprocess
import sys
from pathlib import Path


def convert_to_pdf(docx_path: str | Path, pdf_path: str | Path) -> str:
    """
    Converts a .docx document to a .pdf file.
    Primary engine: docx2pdf (Requires MS Word on Windows/macOS).
    Fallback engine: LibreOffice CLI ('soffice' / 'libreoffice').
    """
    docx_path = Path(docx_path).resolve()
    pdf_path = Path(pdf_path).resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    if not docx_path.exists():
        raise FileNotFoundError(f"Source DOCX file not found: {docx_path}")

    # Primary conversion attempt: docx2pdf
    try:
        from docx2pdf import convert
        print(f"[PDFConverter] Attempting conversion using docx2pdf...")
        convert(str(docx_path), str(pdf_path))
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            print(f"[PDFConverter] Successfully converted PDF via docx2pdf: {pdf_path}")
            return str(pdf_path)
    except Exception as e:
        print(f"[PDFConverter] docx2pdf conversion failed/unavailable ({e}). Trying fallback engine...")

    # Fallback conversion attempt: LibreOffice CLI
    libreoffice_bin = shutil.which("soffice") or shutil.which("libreoffice")
    if libreoffice_bin:
        try:
            print(f"[PDFConverter] Attempting conversion using LibreOffice ({libreoffice_bin})...")
            cmd = [
                libreoffice_bin,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(pdf_path.parent),
                str(docx_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                # LibreOffice defaults output filename to same stem + .pdf
                generated_pdf = pdf_path.parent / f"{docx_path.stem}.pdf"
                if generated_pdf.exists():
                    if generated_pdf != pdf_path:
                        if pdf_path.exists():
                            pdf_path.unlink()
                        generated_pdf.rename(pdf_path)
                    print(f"[PDFConverter] Successfully converted PDF via LibreOffice: {pdf_path}")
                    return str(pdf_path)
            else:
                print(f"[PDFConverter] LibreOffice command error: {result.stderr}")
        except Exception as lo_err:
            print(f"[PDFConverter] LibreOffice conversion error: {lo_err}")

    # If both engines failed
    raise RuntimeError(
        "Gagal mengonversi file .docx ke .pdf!\n"
        "Pastikan Microsoft Word (dengan python package docx2pdf) atau LibreOffice terinstall di sistem Anda."
    )
