import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

import config
from database.reports import save_report_metadata

def generate_pdf_report(detection_data: dict, user_name: str = "Registered User") -> str:
    """
    Generates a professional forensic PDF analysis report using ReportLab.
    Saves PDF file to results/pdf_reports and registers record in MySQL database.
    Returns generated PDF file path.
    """
    detection_id = detection_data.get("detection_id", 0)
    filename_prefix = f"report_det_{detection_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(config.REPORTS_DIR, filename_prefix)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_dark_navy = colors.HexColor("#0A1128")
    c_accent_blue = colors.HexColor("#1282A2")
    c_text_dark = colors.HexColor("#1E293B")
    c_gray_bg = colors.HexColor("#F8FAFC")
    
    res_val = str(detection_data.get("result", "UNCERTAIN")).upper()
    if res_val == "AUTHENTIC":
        c_result = colors.HexColor("#059669")
    elif res_val in ["MANIPULATED", "SYNTHETIC"]:
        c_result = colors.HexColor("#DC2626")
    else:
        c_result = colors.HexColor("#6B7280")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=c_dark_navy,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=12,
        textColor=c_accent_blue,
        spaceAfter=12
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=c_dark_navy,
        spaceBefore=10,
        spaceAfter=6
    )

    normal_text = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=c_text_dark
    )

    disclaimer_style = ParagraphStyle(
        'DisclaimerText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#475569")
    )

    elements = []

    # Header Section
    elements.append(Paragraph(config.APP_TITLE, title_style))
    elements.append(Paragraph(f"FORENSIC ANALYSIS REPORT • {config.APP_SUBTITLE}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=c_accent_blue, spaceBefore=0, spaceAfter=15))

    # General Inspection Metadata Table
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    meta_table_data = [
        [Paragraph("<b>Report Ref ID:</b>", normal_text), Paragraph(f"DET-{detection_id:06d}", normal_text),
         Paragraph("<b>Date & Time:</b>", normal_text), Paragraph(now_str, normal_text)],
        [Paragraph("<b>Inspected By:</b>", normal_text), Paragraph(user_name, normal_text),
         Paragraph("<b>Media Type:</b>", normal_text), Paragraph(str(detection_data.get("media_type")), normal_text)],
        [Paragraph("<b>File Name:</b>", normal_text), Paragraph(str(detection_data.get("file_name")), normal_text),
         Paragraph("<b>Processing Time:</b>", normal_text), Paragraph(str(detection_data.get("processing_time")), normal_text)]
    ]

    meta_table = Table(meta_table_data, colWidths=[1.3*inch, 2.3*inch, 1.3*inch, 2.3*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_gray_bg),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 15))

    # Executive Summary / Detection Result Box
    elements.append(Paragraph("AI Forensics Executive Summary", section_heading))
    
    res_box_style = ParagraphStyle(
        'ResultBoxText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        textColor=c_result,
        alignment=1 # Centered
    )

    res_card_data = [
        [Paragraph("ANALYSIS RESULT", ParagraphStyle('H', fontName='Helvetica-Bold', fontSize=10, textColor=colors.gray, alignment=1))],
        [Paragraph(f"<b>{res_val}</b>", res_box_style)],
        [Paragraph(f"Model Confidence Score: <b>{detection_data.get('confidence')}</b> &nbsp;&nbsp;|&nbsp;&nbsp; Manipulation Probability: <b>{detection_data.get('manipulation_probability')}</b>", ParagraphStyle('Sub', fontName='Helvetica', fontSize=9.5, alignment=1))]
    ]
    res_card_table = Table(res_card_data, colWidths=[7.2*inch])
    res_card_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1.5, c_result),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(res_card_table)
    elements.append(Spacer(1, 15))

    # Technical Details Table
    elements.append(Paragraph("Technical Inspection Breakdown", section_heading))

    tech_rows = [
        [Paragraph("<b>Metric / Parameter</b>", normal_text), Paragraph("<b>Inspection Value</b>", normal_text)],
        [Paragraph("AI Classifier Model", normal_text), Paragraph(str(detection_data.get("model_name")), normal_text)],
        [Paragraph("Confidence Score", normal_text), Paragraph(str(detection_data.get("confidence")), normal_text)],
        [Paragraph("Manipulation Probability", normal_text), Paragraph(str(detection_data.get("manipulation_probability")), normal_text)],
        [Paragraph("Inference Duration", normal_text), Paragraph(str(detection_data.get("processing_time")), normal_text)]
    ]

    if detection_data.get("media_type") == "IMAGE":
        tech_rows.append([Paragraph("Dimensions", normal_text), Paragraph(str(detection_data.get("dimensions", "N/A")), normal_text)])
        tech_rows.append([Paragraph("File Size", normal_text), Paragraph(str(detection_data.get("file_size", "N/A")), normal_text)])
        tech_rows.append([Paragraph("ELA Variance Score", normal_text), Paragraph(str(detection_data.get("ela_variance", "N/A")), normal_text)])
    elif detection_data.get("media_type") == "VIDEO":
        tech_rows.append([Paragraph("Duration", normal_text), Paragraph(str(detection_data.get("duration", "N/A")), normal_text)])
        tech_rows.append([Paragraph("FPS / Resolution", normal_text), Paragraph(f"{detection_data.get('fps')} fps @ {detection_data.get('resolution')}", normal_text)])
        tech_rows.append([Paragraph("Frames Analyzed", normal_text), Paragraph(str(detection_data.get("frames_analyzed", "N/A")), normal_text)])
        tech_rows.append([Paragraph("Suspicious Frames Flagged", normal_text), Paragraph(str(detection_data.get("suspicious_frames_count", "N/A")), normal_text)])
    elif detection_data.get("media_type") == "AUDIO":
        tech_rows.append([Paragraph("Duration", normal_text), Paragraph(str(detection_data.get("duration", "N/A")), normal_text)])
        tech_rows.append([Paragraph("Sample Rate", normal_text), Paragraph(str(detection_data.get("sample_rate", "N/A")), normal_text)])
        tech_rows.append([Paragraph("Spectral Centroid", normal_text), Paragraph(str(detection_data.get("spectral_centroid", "N/A")), normal_text)])
        tech_rows.append([Paragraph("Zero Crossing Rate", normal_text), Paragraph(str(detection_data.get("zero_crossing_rate", "N/A")), normal_text)])

    tech_table = Table(tech_rows, colWidths=[3.2*inch, 4.0*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), c_accent_blue),
        ('TEXTCOLOR', (0,0), (1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(tech_table)
    elements.append(Spacer(1, 20))

    # Mandatory Legal Disclaimer
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceBefore=10, spaceAfter=10))
    disclaimer_text = (
        "<b>SYSTEM DISCLAIMER:</b> This system provides an AI-based estimation of whether digital media "
        "may have been manipulated. Detection results are not guaranteed to be 100% accurate and should "
        "not be treated as definitive forensic evidence."
    )
    elements.append(Paragraph(disclaimer_text, disclaimer_style))

    doc.build(elements)

    # Register report metadata in MySQL
    if detection_id:
        save_report_metadata(detection_id, pdf_path)

    return pdf_path
