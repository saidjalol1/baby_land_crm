from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.units import inch

def generate_pdf(request, queryset):
    # Create a BytesIO buffer to hold the PDF data
    buffer = BytesIO()
    
    # Create a PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # List to hold elements for the PDF
    elements = []
    
    # Define styles for the PDF
    styles = getSampleStyleSheet()
    
    # Add title to the PDF
    title = Paragraph("Chiqimlar Hisoboti", styles['Title'])
    elements.append(title)
    
    # Create table data
    data = [["Nomi", "Summasi", "Sanasi"]]  
    
    # Add rows to the table
    for expance in queryset:
        data.append([expance.name, expance.amount, expance.date_added.strftime('%Y-%m-%d')])
    
    # Create a Table object
    table = Table(data)
    
    # Define the table style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#ccf8fe'),  # Header background color
        ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),   # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),        # Center align all cells
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header font
        ('GRID', (0, 0), (-1, -1), 1, (0, 0, 0)),     # Table grid
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),       # Vertical alignment
    ])
    table.setStyle(style)
    
    # Adjust column widths to ensure the table spans the full page width
    total_width = doc.width
    num_cols = len(data[0])
    col_widths = [total_width / num_cols] * num_cols  # Set equal width for each column
    table._argW = col_widths  # Apply the column widths

    # Add table to elements list
    elements.append(table)
    
    # Build the PDF
    doc.build(elements)
    
    # Return the PDF as an HttpResponse
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="expances_report.pdf"'
    return response

def generate_check_pdf(request, sale):
    # Create a BytesIO buffer to hold the PDF data
    buffer = BytesIO()
    
    # Create a PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # List to hold elements for the PDF
    elements = []
    
    # Define styles for the PDF
    styles = getSampleStyleSheet()
    
    # Add title to the PDF
    title = Paragraph(f"Check - {sale.id}", styles['Title'])
    elements.append(title)
    
    # Add sale details
    elements.append(Paragraph(f"Date: {sale.date_added.strftime('%Y-%m-%d')}", styles['Normal']))
    elements.append(Paragraph(f"Customer: {sale.shop.name } {sale.shop.last_name}", styles['Normal']))
    
    # Create table data for sale items
    data = [["#", "Tovar", "Soni", "Summasi"]]  
    
    # Add rows to the table
    for i, item in enumerate(sale.items.all(), start=1):
        data.append([i, item.product.name, item.quantity, item.get_amount])
    
    # Create a Table object
    table = Table(data)
    
    # Define the table style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#ccf8fe'),  # Header background color
        ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),   # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),        # Center align all cells
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header font
        ('GRID', (0, 0), (-1, -1), 1, (0, 0, 0)),     # Table grid
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),       # Vertical alignment
    ])
    table.setStyle(style)
    
    # Adjust column widths to ensure the table spans the full page width
    total_width = doc.width
    num_cols = len(data[0])
    col_widths = [total_width / num_cols] * num_cols  # Set equal width for each column
    table._argW = col_widths  # Apply the column widths

    # Add table to elements list
    elements.append(table)
    
    # Build the PDF
    doc.build(elements)
    
    # Return the PDF as an HttpResponse
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="sale_{sale.id}.pdf"'
    return response