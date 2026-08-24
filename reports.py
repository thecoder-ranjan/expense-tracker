import csv
import io
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_csv(expenses):
    """Generates a CSV string from a list of expenses."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["ID", "Date", "Category", "Amount", "Description"])
    
    # Write rows
    for exp in expenses:
        writer.writerow([
            exp.get("id"),
            exp.get("date"),
            exp.get("category"),
            exp.get("amount"),
            exp.get("description", "")
        ])
    
    return output.getvalue().encode('utf-8')

def generate_pdf(username, month_year, expenses, category_breakdown, budget_status):
    """Generates a styled PDF report using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles for modern design
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1E293B'), # Slate 800
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        name='SubtitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#64748B'), # Slate 500
        spaceAfter=30
    )
    
    h2_style = ParagraphStyle(
        name='H2Style',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0F172A'), # Slate 900
        spaceBefore=15,
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        name='BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155') # Slate 700
    )
    
    bold_body_style = ParagraphStyle(
        name='BoldBodyStyle',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    table_header_style = ParagraphStyle(
        name='TableHeaderStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.white
    )

    story = []
    
    # Header Section
    story.append(Paragraph("Expense Tracker Monthly Report", title_style))
    formatted_date = datetime.strptime(month_year, "%Y-%m").strftime("%B %Y")
    story.append(Paragraph(f"Prepared for: <b>{username.capitalize()}</b>  |  Reporting Period: <b>{formatted_date}</b>  |  Generated on: {datetime.now().strftime('%Y-%m-%d')}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Summary Metrics Cards
    total_spent = sum(exp['amount'] for exp in expenses)
    num_expenses = len(expenses)
    avg_expense = total_spent / num_expenses if num_expenses > 0 else 0
    max_expense = max((exp['amount'] for exp in expenses), default=0)
    
    summary_data = [
        [
            Paragraph("<b>Total Spending</b>", body_style),
            Paragraph("<b>Total Transactions</b>", body_style),
            Paragraph("<b>Average Transaction</b>", body_style),
            Paragraph("<b>Largest Expense</b>", body_style)
        ],
        [
            Paragraph(f"<font size=14 color='#EF4444'><b>${total_spent:,.2f}</b></font>", body_style),
            Paragraph(f"<font size=14 color='#3B82F6'><b>{num_expenses}</b></font>", body_style),
            Paragraph(f"<font size=14 color='#10B981'><b>${avg_expense:,.2f}</b></font>", body_style),
            Paragraph(f"<font size=14 color='#F59E0B'><b>${max_expense:,.2f}</b></font>", body_style)
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[130, 130, 130, 130])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 12),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 25))
    
    # Category Breakdown
    story.append(Paragraph("Category Spending Breakdown", h2_style))
    if not category_breakdown.empty:
        cat_data = [[
            Paragraph("Category", table_header_style),
            Paragraph("Total Spent", table_header_style),
            Paragraph("Budget Limit", table_header_style),
            Paragraph("% of Budget Used", table_header_style)
        ]]
        
        for index, row in category_breakdown.iterrows():
            cat = row['Category']
            spent = row['Spent']
            
            # Find budget limit from budget_status dict
            limit_val = budget_status.get(cat, {}).get('limit', 0.0)
            limit_str = f"${limit_val:,.2f}" if limit_val > 0 else "N/A"
            
            pct_used = (spent / limit_val) * 100 if limit_val > 0 else 0
            if limit_val > 0:
                if pct_used >= 100:
                    pct_str = f"<font color='#EF4444'><b>{pct_used:.1f}% (Over)</b></font>"
                elif pct_used >= 80:
                    pct_str = f"<font color='#F59E0B'><b>{pct_used:.1f}% (Warning)</b></font>"
                else:
                    pct_str = f"<font color='#10B981'><b>{pct_used:.1f}%</b></font>"
            else:
                pct_str = "No Budget"
                
            cat_data.append([
                Paragraph(cat, body_style),
                Paragraph(f"${spent:,.2f}", body_style),
                Paragraph(limit_str, body_style),
                Paragraph(pct_str, body_style)
            ])
            
        cat_table = Table(cat_data, colWidths=[150, 120, 120, 130])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        story.append(cat_table)
    else:
        story.append(Paragraph("No category data available.", body_style))
        
    story.append(Spacer(1, 25))
    
    # Detailed Expenses
    story.append(Paragraph("Detailed Transactions List", h2_style))
    if expenses:
        exp_data = [[
            Paragraph("Date", table_header_style),
            Paragraph("Category", table_header_style),
            Paragraph("Description", table_header_style),
            Paragraph("Amount", table_header_style)
        ]]
        
        for exp in expenses:
            exp_data.append([
                Paragraph(exp['date'], body_style),
                Paragraph(exp['category'], body_style),
                Paragraph(exp.get('description', '') or '-', body_style),
                Paragraph(f"<b>${exp['amount']:,.2f}</b>", body_style)
            ])
            
        exp_table = Table(exp_data, colWidths=[90, 110, 210, 110])
        exp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#475569')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        story.append(exp_table)
    else:
        story.append(Paragraph("No transactions recorded for this period.", body_style))
        
    # Build Document
    doc.build(story)
    pdf_val = buffer.getvalue()
    buffer.close()
    return pdf_val
