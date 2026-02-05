from io import BytesIO
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from datetime import datetime
import pandas as pd


def export_csv(bills_df):
    """Export bills dataframe to CSV format."""
    return bills_df.to_csv(index=False).encode("utf-8")


def export_excel(bills_df):
    """Export bills dataframe to Excel format."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        bills_df.to_excel(writer, index=False, sheet_name="Bills")
    return output.getvalue()


def export_pdf(bills_df):
    """Export bills dataframe to PDF format using ReportLab in landscape orientation."""
    pdf_buffer = BytesIO()
    
    # Define explicit landscape dimensions (swap width and height)
    # A4 portrait: 595 x 842 points -> landscape: 842 x 595 points
    LANDSCAPE_WIDTH = 842
    LANDSCAPE_HEIGHT = 595
    landscape_pagesize = (LANDSCAPE_WIDTH, LANDSCAPE_HEIGHT)
    
    # Create PDF document with explicit landscape orientation
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape_pagesize,
        rightMargin=0.2*inch,
        leftMargin=0.2*inch,
        topMargin=0.3*inch,
        bottomMargin=0.3*inch,
        title="Bills Export"
    )
    
    # Container for PDF elements
    elements = []
    
    # Add title
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=12,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=4,
        alignment=1  # Center alignment
    )
    elements.append(Paragraph("Receipt & Invoice Export", title_style))
    
    # Add export date
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=8,
        alignment=1  # Center alignment
    )
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
    elements.append(Spacer(1, 0.05*inch))
    
    # Prepare table data
    table_data = []
    
    # Add header row
    headers = [str(h)[:20] for h in bills_df.columns]  # Truncate header names
    table_data.append(headers)
    
    # Add data rows
    for _, row in bills_df.iterrows():
        table_data.append([str(val)[:30] for val in row.values])  # Truncate values
    
    # Calculate optimal column widths using landscape width
    available_width = LANDSCAPE_WIDTH - 0.4*inch
    col_count = len(headers)
    col_width = available_width / col_count if col_count > 0 else available_width
    col_widths = [col_width] * col_count
    
    # Create table with calculated column widths
    table = Table(table_data, colWidths=col_widths, repeatRows=1, splitByRow=False)
    
    # Style the table for compact display
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
        ('TOPPADDING', (0, 0), (-1, 0), 3),
        ('LEFTPADDING', (0, 0), (-1, 0), 1),
        ('RIGHTPADDING', (0, 0), (-1, 0), 1),
        
        # Data rows styling - very compact
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 5),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 1),
        ('LEFTPADDING', (0, 1), (-1, -1), 1),
        ('RIGHTPADDING', (0, 1), (-1, -1), 1),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f5f9')]),
        
        # Borders - very thin
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#d0d0d0')),
        ('LINEABOVE', (0, 0), (-1, 0), 0.8, colors.HexColor('#1f77b4')),
        ('LINEBELOW', (0, -1), (-1, -1), 0.8, colors.HexColor('#1f77b4')),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    return pdf_buffer.getvalue()


def export_detailed_csv(bills_df, items_df):
    """Export detailed bills with line items to CSV format."""
    output = BytesIO()
    
    # Create a combined detailed view
    detailed_data = []
    for _, bill in bills_df.iterrows():
        bill_id = bill.get('id')
        bill_items = items_df[items_df['bill_id'] == bill_id] if 'bill_id' in items_df.columns else []
        
        if len(bill_items) > 0:
            for _, item in bill_items.iterrows():
                detailed_data.append({
                    'Bill_ID': bill_id,
                    'Invoice_Number': bill.get('invoice_number', ''),
                    'Vendor_Name': bill.get('vendor_name', ''),
                    'Purchase_Date': bill.get('purchase_date', ''),
                    'Purchase_Time': bill.get('purchase_time', ''),
                    'Payment_Method': bill.get('payment_method', ''),
                    'Bill_Subtotal': bill.get('subtotal', ''),
                    'Bill_Tax': bill.get('tax_amount', ''),
                    'Bill_Total': bill.get('total_amount', ''),
                    'Currency': bill.get('currency', ''),
                    'Item_SNo': item.get('s_no', ''),
                    'Item_Name': item.get('item_name', ''),
                    'Item_Quantity': item.get('quantity', ''),
                    'Item_Unit_Price': item.get('unit_price', ''),
                    'Item_Total': item.get('item_total', '')
                })
        else:
            # Bill without line items
            detailed_data.append({
                'Bill_ID': bill_id,
                'Invoice_Number': bill.get('invoice_number', ''),
                'Vendor_Name': bill.get('vendor_name', ''),
                'Purchase_Date': bill.get('purchase_date', ''),
                'Purchase_Time': bill.get('purchase_time', ''),
                'Payment_Method': bill.get('payment_method', ''),
                'Bill_Subtotal': bill.get('subtotal', ''),
                'Bill_Tax': bill.get('tax_amount', ''),
                'Bill_Total': bill.get('total_amount', ''),
                'Currency': bill.get('currency', ''),
                'Item_SNo': '',
                'Item_Name': 'No line items',
                'Item_Quantity': '',
                'Item_Unit_Price': '',
                'Item_Total': ''
            })
    
    detailed_df = pd.DataFrame(detailed_data)
    return detailed_df.to_csv(index=False).encode("utf-8")


def export_detailed_excel(bills_df, items_df):
    """Export detailed bills with line items to Excel format with multiple sheets."""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # Sheet 1: Bills Summary
        bills_df.to_excel(writer, index=False, sheet_name="Bills Summary")
        
        # Sheet 2: Line Items
        items_df.to_excel(writer, index=False, sheet_name="Line Items")
        
        # Sheet 3: Detailed Combined View
        detailed_data = []
        for _, bill in bills_df.iterrows():
            bill_id = bill.get('id')
            bill_items = items_df[items_df['bill_id'] == bill_id] if 'bill_id' in items_df.columns else []
            
            if len(bill_items) > 0:
                for _, item in bill_items.iterrows():
                    detailed_data.append({
                        'Bill_ID': bill_id,
                        'Invoice_Number': bill.get('invoice_number', ''),
                        'Vendor_Name': bill.get('vendor_name', ''),
                        'Purchase_Date': bill.get('purchase_date', ''),
                        'Bill_Total': bill.get('total_amount', ''),
                        'Item_Name': item.get('item_name', ''),
                        'Quantity': item.get('quantity', ''),
                        'Unit_Price': item.get('unit_price', ''),
                        'Item_Total': item.get('item_total', '')
                    })
        
        if detailed_data:
            detailed_df = pd.DataFrame(detailed_data)
            detailed_df.to_excel(writer, index=False, sheet_name="Detailed View")
    
    return output.getvalue()


def export_detailed_pdf(bills_df, items_df):
    """Export detailed bills with line items to PDF format."""
    pdf_buffer = BytesIO()
    
    # Define explicit landscape dimensions
    LANDSCAPE_WIDTH = 842
    LANDSCAPE_HEIGHT = 595
    landscape_pagesize = (LANDSCAPE_WIDTH, LANDSCAPE_HEIGHT)
    
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape_pagesize,
        rightMargin=0.2*inch,
        leftMargin=0.2*inch,
        topMargin=0.3*inch,
        bottomMargin=0.3*inch,
        title="Detailed Bills Export"
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        alignment=1
    )
    elements.append(Paragraph("Detailed Bills & Line Items Export", title_style))
    
    # Export date
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=10,
        alignment=1
    )
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Create detailed data for each bill
    for _, bill in bills_df.iterrows():
        bill_id = bill.get('id')
        
        # Bill header
        bill_header_style = ParagraphStyle(
            'BillHeader',
            parent=styles['Heading2'],
            fontSize=10,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=4,
            spaceBefore=8
        )
        bill_info = f"Bill #{bill_id} • {bill.get('vendor_name', 'N/A')} • {bill.get('purchase_date', 'N/A')} • Total: ${float(bill.get('total_amount', 0)):.2f}"
        elements.append(Paragraph(bill_info, bill_header_style))
        
        # Line items for this bill
        bill_items = items_df[items_df['bill_id'] == bill_id] if 'bill_id' in items_df.columns else pd.DataFrame()
        
        if not bill_items.empty:
            # Create table for line items
            item_data = [['S.No', 'Item Name', 'Qty', 'Unit Price', 'Total']]
            for _, item in bill_items.iterrows():
                item_data.append([
                    str(item.get('s_no', '')),
                    str(item.get('item_name', ''))[:40],
                    str(item.get('quantity', '')),
                    f"${float(item.get('unit_price', 0)):.2f}",
                    f"${float(item.get('item_total', 0)):.2f}"
                ])
            
            item_table = Table(item_data, colWidths=[40, 280, 50, 70, 70])
            item_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f4f8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 7),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
            ]))
            elements.append(item_table)
        else:
            elements.append(Paragraph("<i>No line items</i>", styles['Italic']))
        
        elements.append(Spacer(1, 0.1*inch))
    
    doc.build(elements)
    return pdf_buffer.getvalue()


def export_bills_pdf_from_db():
    """Legacy function for PDF export from database."""
    # This function is kept for backward compatibility
    # Use export_pdf() instead
    pass
