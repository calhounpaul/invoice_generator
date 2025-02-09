import os
import json
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Global configuration
MARGINS = {
    'right': 30,
    'left': 30,
    'top': 30,
    'bottom': 30
}

# Font configuration (similar to resume maker)
FONT_NAME = 'LibreBaskerville'
FONT_FILE = 'fonts/LibreBaskerville-Regular.ttf'
FONT_BOLD_FILE = 'fonts/LibreBaskerville-Bold.ttf'
FONT_ITALIC_FILE = 'fonts/LibreBaskerville-Italic.ttf'

# Register fonts
pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))
pdfmetrics.registerFont(TTFont(f'{FONT_NAME}-Bold', FONT_BOLD_FILE))
pdfmetrics.registerFont(TTFont(f'{FONT_NAME}-Italic', FONT_ITALIC_FILE))
pdfmetrics.registerFontFamily(FONT_NAME, normal=FONT_NAME, bold=f'{FONT_NAME}-Bold', italic=f'{FONT_NAME}-Italic')

def create_invoice(company_data, invoice_data, output_dir='outputs'):
    """Generate a PDF invoice with the given data."""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(output_dir, f"Invoice_{invoice_data['invoice_number']}_{timestamp}.pdf")
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=MARGINS['right'],
        leftMargin=MARGINS['left'],
        topMargin=MARGINS['top'],
        bottomMargin=MARGINS['bottom']
    )
    
    # Initialize styles
    styles = getSampleStyleSheet()
    
    # Modify existing Normal style instead of creating new one
    styles['Normal'].fontName = FONT_NAME
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 14
    
    # Add custom styles
    styles.add(ParagraphStyle(
        'CompanyName',
        parent=styles['Normal'],
        fontSize=16,
        leading=20,
        alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Normal'],
        fontName=f'{FONT_NAME}-Bold',
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        spaceAfter=20
    ))
    styles.add(ParagraphStyle(
        'RightAlign',
        parent=styles['Normal'],
        alignment=TA_RIGHT
    ))
    
    story = []
    
    # Add logo if provided
    if company_data.get('logo_path'):
        try:
            img = Image(company_data['logo_path'])
            #keep aspect ratio, scale to max of 3 inch in width and max of 1 inch in height
            height_to_width_ratio = img.drawHeight / img.drawWidth
            if img.drawWidth > 3*inch:
                img.drawWidth = 3*inch
                img.drawHeight = img.drawWidth * height_to_width_ratio
            if img.drawHeight > 1*inch:
                img.drawHeight = 1*inch
                img.drawWidth = img.drawHeight / height_to_width_ratio
            story.append(img)
        except:
            print("Warning: Logo file not found or could not be loaded")
    
    # Company information
    story.append(Paragraph(company_data['name'], styles['CompanyName']))
    story.append(Paragraph(company_data['address'], styles['Normal']))
    story.append(Paragraph(f"Email: {company_data['email']}", styles['Normal']))
    ein_last_four = company_data['tax_id'][-4:]
    stars_preceeding_ein = "**-" + "*" * (len(company_data['tax_id']) - 4 - 3)
    story.append(Paragraph(f"EIN: {stars_preceeding_ein}{ein_last_four}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Invoice header
    story.append(Paragraph("INVOICE", styles['InvoiceTitle']))
    
    # Invoice details and client information
    invoice_details = [
        ['Invoice Number:', invoice_data['invoice_number']],
        ['Date:', invoice_data['date']],
        ['Due Date:', invoice_data['due_date']],
        ['Bill To:', invoice_data['client_name']],
        ['', invoice_data['client_address']],
    ]
    
    t = Table(invoice_details, colWidths=[100, 400])
    t.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    
    # Services table
    services_header = ['Date', 'Description', 'Hours', 'Rate', 'Amount']
    services_data = [services_header]
    
    total_amount = 0
    for service in invoice_data['services']:
        amount = service.get('hours', 0) * service.get('rate', 0) if 'hours' in service else service.get('amount', 0)
        total_amount += amount
        
        row = [
            service.get('date', ''),
            service.get('description', ''),
            str(service.get('hours', '')) if 'hours' in service else '',
            f"${service.get('rate', 0):,.2f}" if 'rate' in service else '',
            f"${amount:,.2f}"
        ]
        services_data.append(row)
    
    # Add total row
    services_data.append(['', '', '', 'Total:', f"${total_amount:,.2f}"])
    
    # Wrap table data in Paragraphs for proper text wrapping
    wrapped_data = []
    for row in services_data:
        if row == services_header:  # Handle header row
            wrapped_row = [Paragraph(str(cell), styles['Normal']) for cell in row]
        else:  # Handle data rows
            wrapped_row = [
                Paragraph(str(row[0]), styles['Normal']),  # Date
                Paragraph(str(row[1]), styles['Normal']),  # Description
                Paragraph(str(row[2]), styles['RightAlign']),  # Hours
                Paragraph(str(row[3]), styles['RightAlign']),  # Rate
                Paragraph(str(row[4]), styles['RightAlign'])   # Amount
            ]
        wrapped_data.append(wrapped_row)

    # Create services table with adjusted column widths
    available_width = 520  # Total width available (letter width minus margins)
    t = Table(wrapped_data, colWidths=[
        available_width * 0.15,  # Date: 15%
        available_width * 0.45,  # Description: 45%
        available_width * 0.12,  # Hours: 12%
        available_width * 0.14,  # Rate: 14%
        available_width * 0.14   # Amount: 14%
    ])
    t.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, 0), f'{FONT_NAME}-Bold'),
        ('FONT', (0, 1), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -2), 0.25, colors.black),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Left align description column
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align text to top of cells
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    
    # Payment status
    if invoice_data.get('payment_status'):
        story.append(Paragraph(
            f"Payment Status: {invoice_data['payment_status']}",
            styles['Normal']
        ))
        if invoice_data.get('payment_date'):
            story.append(Paragraph(
                f"Payment Date: {invoice_data['payment_date']}",
                styles['Normal']
            ))
    
    # Terms and conditions
    story.append(Spacer(1, 30))
    story.append(Paragraph("Terms and Conditions", styles['Normal']))
    for term in company_data['terms']:
        story.append(Paragraph(f"• {term}", styles['Normal']))
    
    # Build the PDF
    doc.build(story)
    print(f"Created invoice: {filename}")
    return filename

# Example usage
if __name__ == "__main__":
    # Load company data
    with open('company_config.json', 'r') as f:
        company_data = json.load(f)
    
    # Create invoice data
    invoice_data = {
        "invoice_number": "INV-2025-003",
        "date": "February 1, 2025",
        "due_date": "None (paid in full)",
        "client_name": "Client who needs boxes folded",
        "client_address": "Client address",
        "services": [
            {
                "date": "January 26, 2025",
                "description": "Starting Bonus",
                "amount": 1000.00
            },
            {
                "date": "January 29, 2025",
                "description": "Initial box-folding consultation call.",
                "hours": 8,
                "rate": 70.00
            },
        ],
        "payment_status": "Paid in Full",
        "payment_dates": [
            "Feb 1, 2025: $480",
            "Jan 30, 2025: $1000",
        ]
    }
    
    create_invoice(company_data, invoice_data)