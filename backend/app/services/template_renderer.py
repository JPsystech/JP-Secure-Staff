"""Template rendering service using Handlebars"""
from pybars import Compiler
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

compiler = Compiler()

def render_template(template_html: str, data: Dict[str, Any]) -> str:
    """
    Render HTML template with data using Handlebars syntax.
    
    Args:
        template_html: HTML template with Handlebars placeholders ({{variable}})
        data: Dictionary with data to fill placeholders
        
    Returns:
        Rendered HTML string
    """
    try:
        template = compiler.compile(template_html)
        rendered = template(data)
        return rendered
    except Exception as e:
        logger.error(f"Template rendering error: {str(e)}")
        raise ValueError(f"Failed to render template: {str(e)}")

