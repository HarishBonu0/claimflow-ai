"""
Document Processing Module
Handles PDF and image text extraction with OCR support.
"""

import os
import logging
from typing import Optional, Dict, Any
import re

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
        'document_type_confidence': 0.0,
        'key_fields': [],
        'missing_info': [],
        'detected_dates': [],
        'detected_amounts': [],
        'extracted_fields': {},
        'verification_score': 0.0,
        'verification_status': 'low_confidence',
    }

    text = document_text or ''
    text_lower = text.lower()

    # Detect document type with lightweight scoring.
    type_hints = {
        'claim_form': ['claim form', 'claim number', 'claimant', 'incident date', 'loss date'],
        'insurance_policy': ['policy', 'premium', 'coverage', 'sum insured', 'policy term'],
        'medical_document': ['medical', 'prescription', 'diagnosis', 'hospital', 'doctor'],
        'bill_invoice': ['invoice', 'bill', 'receipt', 'amount due', 'total amount'],
    }
    type_scores = {}
    for doc_type, hints in type_hints.items():
        score = sum(1 for hint in hints if hint in text_lower)
        type_scores[doc_type] = score

    best_type = max(type_scores, key=type_scores.get)
    best_score = type_scores[best_type]
    if best_score > 0:
        analysis['document_type'] = best_type
        analysis['document_type_confidence'] = min(1.0, best_score / 4.0)

    def _extract_with_patterns(patterns: list[str]) -> str:
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value:
                    return value
        return ''

    # Structured extraction schema with simple confidence heuristics.
    extracted_fields = {
        'policy_number': _extract_with_patterns([
            r'policy\s*(?:number|no\.?|#)\s*[:\-]?\s*([A-Z0-9\-/]{5,})',
        ]),
        'claim_number': _extract_with_patterns([
            r'claim\s*(?:number|no\.?|id|#)\s*[:\-]?\s*([A-Z0-9\-/]{4,})',
        ]),
        'claimant_name': _extract_with_patterns([
            r'(?:claimant|insured|name)\s*[:\-]\s*([A-Za-z .]{3,60})',
        ]),
        'email': _extract_with_patterns([
            r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})',
        ]),
        'phone': _extract_with_patterns([
            r'(?:\+?91[-\s]?)?([6-9]\d{9})',
        ]),
    }

    amounts = re.findall(r'₹\s*[\d,]+(?:\.\d{2})?|\$\s*[\d,]+(?:\.\d{2})?', text)
    dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text)

    extracted_fields['invoice_total'] = amounts[0] if amounts else ''
    extracted_fields['incident_date'] = dates[0] if dates else ''

    analysis['detected_amounts'] = amounts[:5]
    analysis['detected_dates'] = dates[:5]

    # Add confidence metadata per extracted field.
    field_confidence = {}
    for field_name, value in extracted_fields.items():
        confidence = 0.0
        if value:
            if field_name in {'policy_number', 'claim_number'}:
                confidence = 0.9
            elif field_name in {'email', 'phone'}:
                confidence = 0.95
            elif field_name in {'invoice_total', 'incident_date'}:
                confidence = 0.85
            else:
                confidence = 0.75
        field_confidence[field_name] = round(confidence, 2)

    analysis['extracted_fields'] = {
        key: {
            'value': extracted_fields[key],
            'confidence': field_confidence[key],
        }
        for key in extracted_fields
    }

    # Build key fields and missing info lists to preserve compatibility.
    for field_name, metadata in analysis['extracted_fields'].items():
        if metadata['value']:
            analysis['key_fields'].append(field_name)

    required_by_type = {
        'claim_form': ['policy_number', 'claim_number', 'claimant_name', 'incident_date'],
        'insurance_policy': ['policy_number', 'claimant_name'],
        'medical_document': ['claimant_name', 'incident_date'],
        'bill_invoice': ['invoice_total', 'incident_date'],
        'unknown': ['policy_number', 'claim_number', 'claimant_name', 'incident_date'],
    }
    required_fields = required_by_type.get(analysis['document_type'], required_by_type['unknown'])
    for field_name in required_fields:
        if not analysis['extracted_fields'][field_name]['value']:
            analysis['missing_info'].append(field_name)

    # Verification score combines type confidence + required-field confidence.
    required_conf_sum = sum(analysis['extracted_fields'][name]['confidence'] for name in required_fields)
    required_conf_avg = required_conf_sum / max(1, len(required_fields))
    verification_score = (0.35 * analysis['document_type_confidence']) + (0.65 * required_conf_avg)
    analysis['verification_score'] = round(verification_score * 100, 1)

    if analysis['verification_score'] >= 80:
        analysis['verification_status'] = 'high_confidence'
    elif analysis['verification_score'] >= 55:
        analysis['verification_status'] = 'medium_confidence'
    else:
        analysis['verification_status'] = 'low_confidence'

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
