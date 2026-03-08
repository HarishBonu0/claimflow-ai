"""
Document Processing Module
Handles PDF and image text extraction with OCR support.
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF file.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Extracted text string
    """
    if not os.path.exists(pdf_path):
        return "Error: PDF file not found."
    
    try:
        import pdfplumber
        
        logger.info(f"Extracting text from PDF: {pdf_path}")
        text_content = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_content.append(f"--- Page {page_num} ---\n{page_text}")
        
        full_text = "\n\n".join(text_content)
        
        if not full_text.strip():
            return "Error: Could not extract text from PDF. The file might be scanned images."
        
        logger.info(f"Extracted {len(full_text)} characters from PDF")
        return full_text.strip()
    
    except ImportError:
        return "Error: pdfplumber not installed. Run: pip install pdfplumber"
    
    except Exception as e:
        logger.error(f"PDF extraction error: {str(e)}", exc_info=True)
        return f"Error: Could not process PDF. {str(e)[:100]}"


def extract_text_from_image(image_path: str, lang: str = 'eng') -> str:
    """
    Extract text from image using OCR (Tesseract).
    
    Args:
        image_path: Path to image file
        lang: OCR language (eng, hin, tel, tam, kan)
    
    Returns:
        Extracted text string
    """
    if not os.path.exists(image_path):
        return "Error: Image file not found."
    
    try:
        from PIL import Image
        import pytesseract
        
        logger.info(f"Extracting text from image: {image_path} (lang={lang})")
        
        # Open image
        image = Image.open(image_path)
        
        # Perform OCR
        text = pytesseract.image_to_string(image, lang=lang)
        
        if not text.strip():
            return "Error: Could not extract text from image. The image might be too blurry or contain no text."
        
        logger.info(f"Extracted {len(text)} characters from image")
        return text.strip()
    
    except ImportError as e:
        if 'PIL' in str(e):
            return "Error: Pillow not installed. Run: pip install Pillow"
        elif 'pytesseract' in str(e):
            return "Error: pytesseract not installed. Run: pip install pytesseract"
        return f"Error: {str(e)}"
    
    except Exception as e:
        logger.error(f"OCR error: {str(e)}", exc_info=True)
        return f"Error: Could not process image. {str(e)[:100]}"


def process_document(file_path: str, file_type: str, ocr_lang: str = 'eng') -> Dict[str, Any]:
    """
    Process uploaded document and extract text.
    
    Args:
        file_path: Path to uploaded file
        file_type: File type (pdf, image)
        ocr_lang: OCR language for images
    
    Returns:
        Dictionary with extracted text and metadata
    """
    result = {
        'success': False,
        'text': '',
        'file_name': os.path.basename(file_path),
        'file_type': file_type,
        'error': None
    }
    
    try:
        if file_type == 'pdf':
            text = extract_text_from_pdf(file_path)
        elif file_type == 'image':
            text = extract_text_from_image(file_path, lang=ocr_lang)
        else:
            result['error'] = f"Unsupported file type: {file_type}"
            return result
        
        if text.startswith("Error:"):
            result['error'] = text
            return result
        
        result['success'] = True
        result['text'] = text
        result['char_count'] = len(text)
        logger.info(f"Document processed successfully: {result['file_name']}")
        
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}", exc_info=True)
        result['error'] = f"Processing failed: {str(e)[:100]}"
    
    return result


def analyze_claim_document(document_text: str) -> Dict[str, Any]:
    """
    Analyze insurance claim document and extract key information.
    
    Args:
        document_text: Extracted text from document
    
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        'document_type': 'unknown',
        'key_fields': [],
        'missing_info': [],
        'detected_dates': [],
        'detected_amounts': [],
    }
    
    # Basic keyword detection
    text_lower = document_text.lower()
    
    # Detect document type
    if any(word in text_lower for word in ['claim form', 'claim number', 'claimant']):
        analysis['document_type'] = 'claim_form'
    elif any(word in text_lower for word in ['policy', 'premium', 'coverage']):
        analysis['document_type'] = 'insurance_policy'
    elif any(word in text_lower for word in ['medical', 'prescription', 'diagnosis']):
        analysis['document_type'] = 'medical_document'
    elif any(word in text_lower for word in ['invoice', 'bill', 'receipt']):
        analysis['document_type'] = 'bill_invoice'
    
    # Detect potential missing fields
    required_fields = {
        'policy number': ['policy number', 'policy no', 'policy#'],
        'claim number': ['claim number', 'claim no', 'claim id'],
        'claimant name': ['name', 'claimant', 'insured'],
        'date': ['date', 'dated'],
    }
    
    for field_name, keywords in required_fields.items():
        if not any(kw in text_lower for kw in keywords):
            analysis['missing_info'].append(field_name)
    
    # Simple amount detection (basic regex)
    import re
    amounts = re.findall(r'₹\s*[\d,]+(?:\.\d{2})?|\$\s*[\d,]+(?:\.\d{2})?', document_text)
    analysis['detected_amounts'] = amounts[:5]  # Limit to 5
    
    # Simple date detection
    dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', document_text)
    analysis['detected_dates'] = dates[:5]  # Limit to 5
    
    return analysis


def get_document_summary(document_text: str, max_chars: int = 500) -> str:
    """
    Generate a brief summary of document content.
    
    Args:
        document_text: Full document text
        max_chars: Maximum characters for summary
    
    Returns:
        Summary string
    """
    if not document_text:
        return "Empty document"
    
    # Get first N characters
    summary = document_text[:max_chars]
    
    if len(document_text) > max_chars:
        summary += "..."
    
    return summary


if __name__ == "__main__":
    # Test document processing
    print("=" * 60)
    print("Document Processor Test")
    print("=" * 60)
    
    # You can add test code here
    print("\nModule loaded successfully.")
    print("Functions available:")
    print("  - extract_text_from_pdf()")
    print("  - extract_text_from_image()")
    print("  - process_document()")
    print("  - analyze_claim_document()")
