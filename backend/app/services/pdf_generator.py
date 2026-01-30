"""
PDF generation service using xhtml2pdf (pisa)

NOTE: Uses xhtml2pdf library which converts HTML/CSS to PDF.
No browser installation required - works reliably on Windows.
"""
import anyio
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


def _xhtml2pdf_sync(html: str) -> bytes:
    """
    Internal sync helper function that runs xhtml2pdf in a worker thread.
    
    This function uses xhtml2pdf (pisa) to convert HTML to PDF.
    
    Args:
        html: HTML content to convert to PDF
        
    Returns:
        PDF bytes
        
    Raises:
        ValueError: If PDF generation fails
    """
    from xhtml2pdf import pisa
    
    out = BytesIO()
    result = pisa.CreatePDF(src=html, dest=out, encoding="utf-8")
    
    if result.err:
        error_msg = f"xhtml2pdf CreatePDF returned errors: {result.err}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    pdf_bytes = out.getvalue()
    
    if not pdf_bytes or len(pdf_bytes) == 0:
        raise ValueError("Generated PDF is empty")
    
    return pdf_bytes


async def generate_pdf_from_html(html: str) -> bytes:
    """
    Generate PDF from HTML string using xhtml2pdf (pisa).
    
    This async wrapper runs the sync xhtml2pdf code in a worker thread using
    anyio.to_thread.run_sync to avoid blocking the event loop.
    
    Args:
        html: HTML content to convert to PDF
        
    Returns:
        PDF bytes
        
    Raises:
        ValueError: If PDF generation fails
    """
    try:
        return await anyio.to_thread.run_sync(_xhtml2pdf_sync, html)
    except ValueError:
        # Re-raise ValueError as-is (already has proper message)
        raise
    except Exception as e:
        logger.exception("PDF generation error")
        raise ValueError(f"Failed to generate PDF: {e}")

