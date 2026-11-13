import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from app.models.asset import Asset


def generate_asset_spec_sheet_pdf(asset: Asset, deprec_info: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=14,
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=6,
    )
    cell_label_style = ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor('#475569'),
    )
    cell_val_style = ParagraphStyle(
        'CellVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#0F172A'),
    )

    elements = []

    # Header
    elements.append(Paragraph(f"AssetTrack Spec Sheet: {asset.name}", title_style))
    elements.append(Paragraph(f"Tag: {asset.asset_tag} | Serial: {asset.serial_number} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=14))

    # General Info Table
    elements.append(Paragraph("General Information", h2_style))
    category_name = asset.category.name if asset.category else "N/A"
    department_name = asset.department.name if asset.department else "Unassigned"
    vendor_name = asset.vendor.name if asset.vendor else "N/A"

    gen_data = [
        [Paragraph("Asset Tag", cell_label_style), Paragraph(str(asset.asset_tag), cell_val_style), Paragraph("Category", cell_label_style), Paragraph(str(category_name), cell_val_style)],
        [Paragraph("Manufacturer", cell_label_style), Paragraph(str(asset.manufacturer), cell_val_style), Paragraph("Model", cell_label_style), Paragraph(str(asset.model), cell_val_style)],
        [Paragraph("Serial Number", cell_label_style), Paragraph(str(asset.serial_number), cell_val_style), Paragraph("Status", cell_label_style), Paragraph(str(asset.status.value), cell_val_style)],
        [Paragraph("Condition", cell_label_style), Paragraph(str(asset.condition.value), cell_val_style), Paragraph("Location", cell_label_style), Paragraph(str(asset.location), cell_val_style)],
        [Paragraph("Department", cell_label_style), Paragraph(str(department_name), cell_val_style), Paragraph("Vendor", cell_label_style), Paragraph(str(vendor_name), cell_val_style)],
    ]
    t1 = Table(gen_data, colWidths=[100, 170, 100, 170])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 14))

    # Financial & Depreciation Information
    elements.append(Paragraph("Financial & Lifecycle Analytics", h2_style))
    fin_data = [
        [Paragraph("Purchase Cost", cell_label_style), Paragraph(f"${float(asset.purchase_cost):,.2f}", cell_val_style), Paragraph("Salvage Value", cell_label_style), Paragraph(f"${float(asset.salvage_value):,.2f}", cell_val_style)],
        [Paragraph("Purchase Date", cell_label_style), Paragraph(str(asset.purchase_date), cell_val_style), Paragraph("Lifespan", cell_label_style), Paragraph(f"{asset.expected_lifespan_months} months", cell_val_style)],
        [Paragraph("Depreciation Method", cell_label_style), Paragraph(str(asset.depreciation_method.value), cell_val_style), Paragraph("Depreciated %", cell_label_style), Paragraph(f"{deprec_info.get('percent_depreciated', 0.0)}%", cell_val_style)],
        [Paragraph("Accumulated Depreciation", cell_label_style), Paragraph(f"${deprec_info.get('accumulated_depreciation', 0.0):,.2f}", cell_val_style), Paragraph("Current Book Value", cell_label_style), Paragraph(f"${deprec_info.get('current_book_value', 0.0):,.2f}", cell_val_style)],
        [Paragraph("Equipment Age", cell_label_style), Paragraph(f"{deprec_info.get('age_months', 0)} months", cell_val_style), Paragraph("Remaining Lifespan", cell_label_style), Paragraph(f"{deprec_info.get('remaining_months', 0)} months", cell_val_style)],
    ]
    t2 = Table(fin_data, colWidths=[100, 170, 100, 170])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 14))

    # Technical Specifications
    elements.append(Paragraph("Hardware / Technical Specifications", h2_style))
    specs = asset.specifications or {}
    if specs:
        spec_rows = []
        for k, v in specs.items():
            spec_rows.append([Paragraph(str(k).replace('_', ' ').title(), cell_label_style), Paragraph(str(v), cell_val_style)])
        t3 = Table(spec_rows, colWidths=[160, 380])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(t3)
    else:
        elements.append(Paragraph("No technical specifications recorded.", cell_val_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_fleet_inventory_pdf(assets: list) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=10,
    )
    th_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.white,
    )
    td_style = ParagraphStyle(
        'TD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#1E293B'),
    )

    elements = [
        Paragraph("AssetTrack Enterprise Fleet Inventory Report", title_style),
        Paragraph(f"Total Assets: {len(assets)} | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}", subtitle_style),
        Spacer(1, 8),
    ]

    header_row = [
        Paragraph("Tag", th_style),
        Paragraph("Name / Model", th_style),
        Paragraph("Serial #", th_style),
        Paragraph("Category", th_style),
        Paragraph("Status", th_style),
        Paragraph("Cost", th_style),
    ]
    data = [header_row]

    total_cost = 0.0
    for a in assets:
        cost = float(a.purchase_cost)
        total_cost += cost
        cat_name = a.category.name if a.category else "N/A"
        data.append([
            Paragraph(a.asset_tag, td_style),
            Paragraph(f"{a.name} ({a.model})", td_style),
            Paragraph(a.serial_number, td_style),
            Paragraph(cat_name, td_style),
            Paragraph(a.status.value, td_style),
            Paragraph(f"${cost:,.2f}", td_style),
        ])

    table = Table(data, colWidths=[70, 160, 90, 80, 80, 60], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>Total Fleet Acquisition Cost:</b> ${total_cost:,.2f}", td_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
