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

# Load PDF configuration
def load_pdf_config(config_path='pdf_config.json'):
    """Load PDF configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)

# Load configuration at module level
PDF_CONFIG = load_pdf_config()

# Register fonts from configuration
FONT_NAME = PDF_CONFIG['fonts']['name']
pdfmetrics.registerFont(TTFont(FONT_NAME, PDF_CONFIG['fonts']['regular']))
pdfmetrics.registerFont(TTFont(f'{FONT_NAME}-Bold', PDF_CONFIG['fonts']['bold']))
pdfmetrics.registerFont(TTFont(f'{FONT_NAME}-Italic', PDF_CONFIG['fonts']['italic']))
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
        rightMargin=PDF_CONFIG['margins']['right'],
        leftMargin=PDF_CONFIG['margins']['left'],
        topMargin=PDF_CONFIG['margins']['top'],
        bottomMargin=PDF_CONFIG['margins']['bottom']
    )
    
    # Initialize styles
    styles = getSampleStyleSheet()

    # Modify existing Normal style instead of creating new one
    styles['Normal'].fontName = FONT_NAME
    styles['Normal'].fontSize = PDF_CONFIG['styles']['normal']['fontSize']
    styles['Normal'].leading = PDF_CONFIG['styles']['normal']['leading']

    # Add custom styles
    alignment_map = {
        'LEFT': TA_LEFT,
        'RIGHT': TA_RIGHT,
        'CENTER': TA_CENTER,
        'JUSTIFY': TA_JUSTIFY
    }

    styles.add(ParagraphStyle(
        'CompanyName',
        parent=styles['Normal'],
        fontSize=PDF_CONFIG['styles']['companyName']['fontSize'],
        leading=PDF_CONFIG['styles']['companyName']['leading'],
        alignment=alignment_map[PDF_CONFIG['styles']['companyName']['alignment']]
    ))

    invoice_title_font = f'{FONT_NAME}-Bold' if PDF_CONFIG['styles']['invoiceTitle'].get('bold', False) else FONT_NAME
    styles.add(ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Normal'],
        fontName=invoice_title_font,
        fontSize=PDF_CONFIG['styles']['invoiceTitle']['fontSize'],
        leading=PDF_CONFIG['styles']['invoiceTitle']['leading'],
        alignment=alignment_map[PDF_CONFIG['styles']['invoiceTitle']['alignment']],
        spaceAfter=PDF_CONFIG['styles']['invoiceTitle']['spaceAfter']
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
            # Keep aspect ratio, scale to max width and height from config
            max_width = PDF_CONFIG['logo']['maxWidth'] * inch
            max_height = PDF_CONFIG['logo']['maxHeight'] * inch
            height_to_width_ratio = img.drawHeight / img.drawWidth
            if img.drawWidth > max_width:
                img.drawWidth = max_width
                img.drawHeight = img.drawWidth * height_to_width_ratio
            if img.drawHeight > max_height:
                img.drawHeight = max_height
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
    story.append(Spacer(1, PDF_CONFIG['spacing']['afterCompanyInfo']))
    
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
    story.append(Spacer(1, PDF_CONFIG['spacing']['afterInvoiceDetails']))

    # Categorize items into services, products, and other charges
    services = []
    products = []
    other_charges = []

    for item in invoice_data['services']:
        if 'hours' in item and 'rate' in item:
            services.append(item)
        elif 'quantity' in item and 'unit_price' in item:
            products.append(item)
        elif 'amount' in item:
            other_charges.append(item)

    # Helper function to create a table section
    def create_table_section(items, header, column_labels, five_column=True):
        """Create a table section with header and subtotal."""
        section_data = [column_labels]
        subtotal = 0

        for item in items:
            # Calculate amount based on item type
            if 'hours' in item and 'rate' in item:
                col3_val = item['hours']
                col4_val = item['rate']
                amount = col3_val * col4_val
            elif 'quantity' in item and 'unit_price' in item:
                col3_val = item['quantity']
                col4_val = item['unit_price']
                amount = col3_val * col4_val
            elif 'amount' in item:
                col3_val = ''
                col4_val = ''
                amount = item['amount']
            else:
                col3_val = ''
                col4_val = ''
                amount = 0

            subtotal += amount

            # Format the row
            if five_column:
                row = [
                    item.get('date', ''),
                    item.get('description', ''),
                    str(col3_val) if col3_val != '' else '',
                    f"${col4_val:,.2f}" if col4_val != '' else '',
                    f"${amount:,.2f}"
                ]
            else:  # Three-column layout for other charges
                row = [
                    item.get('date', ''),
                    item.get('description', ''),
                    f"${amount:,.2f}"
                ]
            section_data.append(row)

        # Add subtotal row
        if five_column:
            section_data.append(['', '', '', f'{header} Subtotal:', f"${subtotal:,.2f}"])
        else:
            section_data.append(['', f'{header} Subtotal:', f"${subtotal:,.2f}"])

        return section_data, subtotal

    # Build tables for each section
    grand_total = 0
    available_width = PDF_CONFIG['table']['availableWidth']
    col_widths = PDF_CONFIG['table']['columnWidths']
    table_style = PDF_CONFIG['table']['style']

    # Professional Services section
    if services:
        story.append(Paragraph("PROFESSIONAL SERVICES", styles['Normal']))
        story.append(Spacer(1, 6))

        services_header = ['Date', 'Description', 'Hours', 'Rate', 'Amount']
        services_data, services_subtotal = create_table_section(services, 'Services', services_header, five_column=True)
        grand_total += services_subtotal

        # Wrap in Paragraphs
        wrapped_data = []
        for row in services_data:
            if row == services_header:
                wrapped_row = [Paragraph(str(cell), styles['Normal']) for cell in row]
            else:
                wrapped_row = [
                    Paragraph(str(row[0]), styles['Normal']),
                    Paragraph(str(row[1]), styles['Normal']),
                    Paragraph(str(row[2]), styles['RightAlign']),
                    Paragraph(str(row[3]), styles['RightAlign']),
                    Paragraph(str(row[4]), styles['RightAlign'])
                ]
            wrapped_data.append(wrapped_row)

        t = Table(wrapped_data, colWidths=[
            available_width * col_widths['date'],
            available_width * col_widths['description'],
            available_width * col_widths['hours'],
            available_width * col_widths['rate'],
            available_width * col_widths['amount']
        ])
        t.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), f'{FONT_NAME}-Bold'),
            ('FONT', (0, 1), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), table_style['headerFontSize']),
            ('GRID', (0, 0), (-1, -1), table_style['gridWidth'], colors.black),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), table_style['topPadding']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), table_style['bottomPadding']),
            ('LEFTPADDING', (0, 0), (-1, -1), table_style['leftPadding']),
            ('RIGHTPADDING', (0, 0), (-1, -1), table_style['rightPadding']),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    # Items & Products section
    if products:
        story.append(Paragraph("ITEMS & PRODUCTS", styles['Normal']))
        story.append(Spacer(1, 6))

        products_header = ['Date', 'Description', 'Qty', 'Unit Price', 'Amount']
        products_data, products_subtotal = create_table_section(products, 'Items', products_header, five_column=True)
        grand_total += products_subtotal

        # Wrap in Paragraphs
        wrapped_data = []
        for row in products_data:
            if row == products_header:
                wrapped_row = [Paragraph(str(cell), styles['Normal']) for cell in row]
            else:
                wrapped_row = [
                    Paragraph(str(row[0]), styles['Normal']),
                    Paragraph(str(row[1]), styles['Normal']),
                    Paragraph(str(row[2]), styles['RightAlign']),
                    Paragraph(str(row[3]), styles['RightAlign']),
                    Paragraph(str(row[4]), styles['RightAlign'])
                ]
            wrapped_data.append(wrapped_row)

        t = Table(wrapped_data, colWidths=[
            available_width * col_widths['date'],
            available_width * col_widths['description'],
            available_width * col_widths['hours'],
            available_width * col_widths['rate'],
            available_width * col_widths['amount']
        ])
        t.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), f'{FONT_NAME}-Bold'),
            ('FONT', (0, 1), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), table_style['headerFontSize']),
            ('GRID', (0, 0), (-1, -1), table_style['gridWidth'], colors.black),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), table_style['topPadding']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), table_style['bottomPadding']),
            ('LEFTPADDING', (0, 0), (-1, -1), table_style['leftPadding']),
            ('RIGHTPADDING', (0, 0), (-1, -1), table_style['rightPadding']),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    # Other Charges section (3-column layout)
    if other_charges:
        story.append(Paragraph("OTHER CHARGES", styles['Normal']))
        story.append(Spacer(1, 6))

        charges_header = ['Date', 'Description', 'Amount']
        charges_data, charges_subtotal = create_table_section(other_charges, 'Charges', charges_header, five_column=False)
        grand_total += charges_subtotal

        # Wrap in Paragraphs
        wrapped_data = []
        for row in charges_data:
            if row == charges_header:
                wrapped_row = [Paragraph(str(cell), styles['Normal']) for cell in row]
            else:
                wrapped_row = [
                    Paragraph(str(row[0]), styles['Normal']),
                    Paragraph(str(row[1]), styles['Normal']),
                    Paragraph(str(row[2]), styles['RightAlign'])
                ]
            wrapped_data.append(wrapped_row)

        # Calculate column widths for 3-column layout
        t = Table(wrapped_data, colWidths=[
            available_width * col_widths['date'],
            available_width * (col_widths['description'] + col_widths['hours'] + col_widths['rate']),
            available_width * col_widths['amount']
        ])
        t.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), f'{FONT_NAME}-Bold'),
            ('FONT', (0, 1), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), table_style['headerFontSize']),
            ('GRID', (0, 0), (-1, -1), table_style['gridWidth'], colors.black),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), table_style['topPadding']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), table_style['bottomPadding']),
            ('LEFTPADDING', (0, 0), (-1, -1), table_style['leftPadding']),
            ('RIGHTPADDING', (0, 0), (-1, -1), table_style['rightPadding']),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    # Grand Total
    total_data = [['', '', '', 'TOTAL DUE:', f"${grand_total:,.2f}"]]
    wrapped_total = [[
        Paragraph('', styles['Normal']),
        Paragraph('', styles['Normal']),
        Paragraph('', styles['Normal']),
        Paragraph('<b>TOTAL DUE:</b>', styles['RightAlign']),
        Paragraph(f'<b>${grand_total:,.2f}</b>', styles['RightAlign'])
    ]]

    t_total = Table(wrapped_total, colWidths=[
        available_width * col_widths['date'],
        available_width * col_widths['description'],
        available_width * col_widths['hours'],
        available_width * col_widths['rate'],
        available_width * col_widths['amount']
    ])
    t_total.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), f'{FONT_NAME}-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEABOVE', (3, 0), (-1, -1), 2, colors.black),
    ]))
    story.append(t_total)
    story.append(Spacer(1, PDF_CONFIG['spacing']['afterServicesTable']))

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
    story.append(Spacer(1, PDF_CONFIG['spacing']['beforeTerms']))
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

    # Load invoice data
    with open('invoice_data.json', 'r') as f:
        invoice_data = json.load(f)

    create_invoice(company_data, invoice_data)
