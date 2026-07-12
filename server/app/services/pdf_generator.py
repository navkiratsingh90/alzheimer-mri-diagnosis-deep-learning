from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import os
import tempfile
from datetime import datetime
import traceback

# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------
PRIMARY_COLOR = colors.HexColor('#0EA472')
SECONDARY_COLOR = colors.HexColor('#0D1B2A')
LIGHT_GRAY = colors.HexColor('#F8FAFB')
MEDIUM_GRAY = colors.HexColor('#64748B')
BORDER_GRAY = colors.HexColor('#E2E8F0')
WHITE = colors.white

SEVERITY_COLORS = {
    "Non Demented":       colors.HexColor('#0EA472'),
    "Very Mild Demented": colors.HexColor('#EAB308'),
    "Mild Demented":      colors.HexColor('#F97316'),
    "Moderate Demented":  colors.HexColor('#DC2626'),
}
DEFAULT_SEVERITY_COLOR = colors.HexColor('#64748B')

def _get_severity_color(result: str):
    return SEVERITY_COLORS.get(result, DEFAULT_SEVERITY_COLOR)

# ---------------------------------------------------------------------------
# Content generators (fallback if AI summary is short)
# ---------------------------------------------------------------------------

def _get_precautions(result: str):
    common = [
        "Maintain a consistent daily routine to support memory and reduce confusion.",
        "Stay physically active — regular movement supports overall brain and cardiovascular health.",
        "Prioritize sleep quality and aim for a consistent sleep schedule.",
        "Engage in mentally stimulating activities — reading, puzzles, learning a new skill, or social conversation.",
        "Maintain a balanced diet rich in fruits, vegetables, and omega-3 sources.",
        "Keep regular follow-up appointments with a neurologist or memory-care specialist.",
    ]
    extra = {
        "Very Mild Demented": [
            "Consider keeping a symptom journal to track any changes over time.",
            "Discuss baseline cognitive testing with a specialist to establish a comparison point for future visits.",
        ],
        "Mild Demented": [
            "Involve a trusted family member or caregiver in medical appointments going forward.",
            "Consider simplifying daily tasks and using reminders (notes, alarms, apps) to reduce cognitive load.",
        ],
        "Moderate Demented": [
            "Begin discussing longer-term care planning and support options with family and a specialist.",
            "Ensure the home environment is safe (reduce fall hazards, label rooms, secure hazardous items).",
            "Consider a formal caregiver support plan, as day-to-day supervision needs may increase.",
        ],
    }
    return common + extra.get(result, [])

def _get_future_outlook(result: str) -> str:
    return {
        "Non Demented": (
            "No signs of concern were found in this analysis. That said, cognitive health can change over "
            "time, so periodic monitoring — especially if any memory or behavioral changes are noticed in "
            "daily life — is still a reasonable precaution, particularly with age or family history factors."
        ),
        "Very Mild Demented": (
            "Very mild-stage changes do not always progress, and in some cases can remain stable for extended "
            "periods. However, regular monitoring is recommended, since early-stage changes can sometimes "
            "advance over time. Establishing a relationship with a specialist now can make future monitoring "
            "more effective."
        ),
        "Mild Demented": (
            "Mild-stage cognitive changes can vary significantly in how they progress from person to person. "
            "With appropriate medical guidance, lifestyle adjustments, and in some cases medication, many "
            "individuals are able to manage symptoms and maintain quality of life for a meaningful period."
        ),
        "Moderate Demented": (
            "Moderate-stage changes typically involve a more noticeable impact on daily functioning, and care "
            "needs often increase over time. Working closely with a specialist to build a care plan — covering "
            "medical management, safety, and family/caregiver support — is strongly advised at this stage."
        ),
    }.get(result, "Outcomes vary by individual — a specialist consultation is the best way to understand what this result may mean going forward.")

RECOMMENDED_CENTERS = [
    ["AIIMS (All India Institute of Medical Sciences)", "New Delhi", "Neurology / Memory Clinic"],
    ["PGIMER", "Chandigarh", "Neurology Department"],
    ["NIMHANS", "Bengaluru", "Neuropsychiatry & Cognitive Disorders"],
    ["Fortis Memory Clinic", "Multiple Cities", "Dedicated Memory & Cognitive Care"],
    ["Apollo Hospitals — Neurology", "Multiple Cities", "Neurology / Memory Assessment"],
]

# ---------------------------------------------------------------------------
# Main report generator
# ---------------------------------------------------------------------------

def generate_pdf_report(title, summary, prediction, output_path):
    output_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(output_dir, exist_ok=True)

    if not title:
        title = "NeuroSight Report"
    if not summary:
        summary = ""

    ts = prediction.get('timestamp')
    if isinstance(ts, datetime):
        date_str_display = ts.strftime("%B %d, %Y at %I:%M %p")
    elif isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            date_str_display = dt.strftime("%B %d, %Y at %I:%M %p")
        except Exception:
            date_str_display = ts
    else:
        date_str_display = "N/A"

    confidence = prediction.get('confidence', 0.0)
    confidence_pct = f"{confidence * 100:.1f}%"
    result = prediction.get('result', 'Unknown')
    severity_color = _get_severity_color(result)

    fd, tmp_path = tempfile.mkstemp(suffix=".pdf", dir=output_dir)
    os.close(fd)

    try:
        doc = SimpleDocTemplate(
            tmp_path,
            pagesize=A4,
            rightMargin=60,
            leftMargin=60,
            topMargin=50,
            bottomMargin=60,
        )

        # --- Styles ---
        styles = getSampleStyleSheet()
        brand_title_style = ParagraphStyle(
            'BrandTitle', parent=styles['Title'], fontSize=26,
            textColor=WHITE, alignment=TA_LEFT, fontName='Helvetica-Bold', leading=30
        )
        brand_subtitle_style = ParagraphStyle(
            'BrandSubtitle', parent=styles['Normal'], fontSize=10.5,
            textColor=WHITE, alignment=TA_LEFT, fontName='Helvetica'
        )
        report_title_style = ParagraphStyle(
            'ReportTitle', parent=styles['Title'], fontSize=18,
            textColor=SECONDARY_COLOR, spaceAfter=4, alignment=TA_LEFT, fontName='Helvetica-Bold'
        )
        heading_style = ParagraphStyle(
            'CustomHeading', parent=styles['Heading2'], fontSize=14,
            textColor=SECONDARY_COLOR, spaceAfter=8, spaceBefore=4, fontName='Helvetica-Bold'
        )
        normal_style = ParagraphStyle(
            'CustomNormal', parent=styles['Normal'], fontSize=10.5,
            textColor=SECONDARY_COLOR, spaceAfter=6, leading=15.5,
            fontName='Helvetica', alignment=TA_JUSTIFY
        )
        bullet_style = ParagraphStyle(
            'Bullet', parent=normal_style, leftIndent=14, spaceAfter=4, alignment=TA_LEFT
        )
        small_style = ParagraphStyle(
            'Small', parent=styles['Normal'], fontSize=9,
            textColor=MEDIUM_GRAY, alignment=TA_LEFT, fontName='Helvetica'
        )
        badge_result_style = ParagraphStyle(
            'BadgeResult', parent=styles['Normal'], fontSize=17,
            textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_LEFT
        )
        badge_label_style = ParagraphStyle(
            'BadgeLabel', parent=styles['Normal'], fontSize=8.5,
            textColor=WHITE, fontName='Helvetica', alignment=TA_LEFT
        )
        disclaimer_style = ParagraphStyle(
            'Disclaimer', parent=styles['Normal'], fontSize=8,
            textColor=colors.grey, alignment=TA_JUSTIFY, fontName='Helvetica-Oblique', leading=11
        )
        table_header_style = ParagraphStyle(
            'TableHeader', parent=styles['Normal'], fontSize=9.5,
            textColor=WHITE, fontName='Helvetica-Bold'
        )
        table_cell_style = ParagraphStyle(
            'TableCell', parent=styles['Normal'], fontSize=9.5,
            textColor=SECONDARY_COLOR, fontName='Helvetica', leading=13
        )
        summary_box_style = ParagraphStyle(
            'SummaryBox', parent=normal_style,
            backColor=LIGHT_GRAY,
            leftIndent=12, rightIndent=12,
            spaceBefore=8, spaceAfter=8,
            leading=16
        )

        def section_header(text, emoji="•"):
            head = Table(
                [[Paragraph(f"{emoji}  {text}", heading_style)]],
                colWidths=[doc.width],
                rowHeights=[22]
            )
            head.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('RADIUS', (0, 0), (-1, -1), 4),
            ]))
            return head

        story = []

        # --- 1. Brand header banner ---
        header_content = Table(
            [[Paragraph("🧠  NeuroSight", brand_title_style)],
             [Paragraph("AI-Powered Alzheimer's MRI Diagnostic Report", brand_subtitle_style)]],
            colWidths=[doc.width]
        )
        header_content.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), SECONDARY_COLOR),
            ('LEFTPADDING', (0, 0), (-1, -1), 16),
            ('RIGHTPADDING', (0, 0), (-1, -1), 16),
            ('TOPPADDING', (0, 0), (0, 0), 16),
            ('BOTTOMPADDING', (0, 0), (0, 0), 2),
            ('TOPPADDING', (0, 1), (0, 1), 2),
            ('BOTTOMPADDING', (0, 1), (0, 1), 16),
        ]))
        accent_stripe = Table([[""]], colWidths=[doc.width], rowHeights=[4])
        accent_stripe.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), PRIMARY_COLOR)]))

        story.append(header_content)
        story.append(accent_stripe)
        story.append(Spacer(1, 18))

        # --- 2. Report title + generated date ---
        story.append(Paragraph(title, report_title_style))
        gen_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        story.append(Paragraph(f"Generated on {gen_date}", small_style))
        story.append(Spacer(1, 16))

        # --- 3. Result badge (color-coded) + confidence bar ---
        confidence_bar_width = doc.width - 40
        filled_width = max(4, confidence_bar_width * min(max(confidence, 0), 1))
        empty_width = confidence_bar_width - filled_width

        confidence_bar = Table(
            [["", ""]], colWidths=[filled_width, empty_width], rowHeights=[10]
        )
        confidence_bar.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), severity_color),
            ('BACKGROUND', (1, 0), (1, 0), BORDER_GRAY),
        ]))

        badge_inner = Table(
            [[Paragraph("DIAGNOSTIC RESULT", badge_label_style)],
             [Paragraph(result, badge_result_style)],
             [Paragraph(f"Model Confidence: {confidence_pct}", badge_label_style)],
             [Spacer(1, 6)],
             [confidence_bar]],
            colWidths=[doc.width - 32]
        )
        badge_inner.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        badge = Table([[badge_inner]], colWidths=[doc.width])
        badge.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), severity_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 16),
            ('RIGHTPADDING', (0, 0), (-1, -1), 16),
            ('TOPPADDING', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
            ('RADIUS', (0, 0), (-1, -1), 6),
        ]))
        story.append(badge)
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Scan date: {date_str_display}", small_style))
        story.append(Spacer(1, 18))

        # --- 4. AI Clinical Summary (now displayed in a shaded box) ---
        story.append(section_header("AI Clinical Summary", "📋"))
        story.append(Spacer(1, 4))
        # If summary is short, expand with static context
        if len(summary.strip()) < 200:
            confidence_pct_display = f"{confidence*100:.1f}%"
            context = {
                "Non Demented": "The scan shows no strong indicators of Alzheimer's-related decline.",
                "Very Mild Demented": "The scan shows early, subtle patterns that may indicate very early cognitive changes.",
                "Mild Demented": "The scan shows patterns consistent with mild cognitive impairment.",
                "Moderate Demented": "The scan shows pronounced patterns consistent with moderate cognitive decline.",
            }
            prefix = context.get(result, "The scan was analyzed and classified.")
            summary = f"{prefix} {summary}"
        story.append(Paragraph(summary, summary_box_style))
        story.append(Spacer(1, 16))

        # --- 5. Scan Image (optional) ---
        img_path = prediction.get('image_path')
        if img_path and os.path.exists(img_path):
            try:
                story.append(section_header("Scan Image", "🖼️"))
                story.append(Spacer(1, 8))
                img = Image(img_path, width=3.2 * inch, height=3.2 * inch, kind='proportional')
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 4))
                story.append(Paragraph("MRI scan used for this prediction", small_style))
                story.append(Spacer(1, 16))
            except Exception as e:
                print(f"Warning: Could not embed image: {e}")

        # --- 6. Precautions & Lifestyle Recommendations ---
        story.append(section_header("Precautions & Lifestyle Recommendations", "✅"))
        story.append(Spacer(1, 8))
        for point in _get_precautions(result):
            story.append(Paragraph(f"•  {point}", bullet_style))
        story.append(Spacer(1, 16))

        # --- 7. What This Could Mean Going Forward ---
        story.append(section_header("What This Could Mean Going Forward", "🔮"))
        story.append(Spacer(1, 8))
        story.append(Paragraph(_get_future_outlook(result), normal_style))
        story.append(Spacer(1, 16))

        # --- 8. Recommended Specialists / Centers ---
        story.append(section_header("Recommended Specialists & Centers", "🏥"))
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            "The following is a general, non-personalized list of well-known neurology and memory-care "
            "centers in India, offered as a starting point for research — not a specific referral. Please "
            "choose a specialist based on your location, insurance, and personal circumstances.",
            small_style
        ))
        story.append(Spacer(1, 8))

        hospital_rows = [[
            Paragraph("Center", table_header_style),
            Paragraph("Location", table_header_style),
            Paragraph("Specialty", table_header_style),
        ]]
        for name, loc, specialty in RECOMMENDED_CENTERS:
            hospital_rows.append([
                Paragraph(name, table_cell_style),
                Paragraph(loc, table_cell_style),
                Paragraph(specialty, table_cell_style),
            ])

        hospital_table = Table(hospital_rows, colWidths=[doc.width * 0.42, doc.width * 0.23, doc.width * 0.35])
        hospital_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), SECONDARY_COLOR),
            ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(hospital_table)
        story.append(Spacer(1, 18))

        # --- 9. Report Details ---
        story.append(section_header("Report Details", "📄"))
        story.append(Spacer(1, 8))
        detail_data = [
            [Paragraph("Result", table_cell_style), Paragraph(result, table_cell_style)],
            [Paragraph("Confidence", table_cell_style), Paragraph(confidence_pct, table_cell_style)],
            [Paragraph("Scan Date", table_cell_style), Paragraph(date_str_display, table_cell_style)],
        ]
        detail_table = Table(detail_data, colWidths=[2 * inch, doc.width - 2 * inch])
        detail_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(detail_table)
        story.append(Spacer(1, 20))

        # --- 10. Disclaimer ---
        story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_GRAY, spaceAfter=8))
        disclaimer = (
            "Disclaimer: This report is generated by an AI model and is for informational purposes only. "
            "It does not replace professional medical advice, diagnosis, or treatment. Precautions, lifestyle "
            "suggestions, and recommended centers listed above are general in nature and not personalized "
            "medical guidance. Always consult a qualified healthcare provider for any medical decisions."
        )
        story.append(Paragraph(disclaimer, disclaimer_style))

        # --- Footer callback ---
        def _header_footer(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.grey)
            canvas.line(60, 38, doc.width + 60, 38)
            canvas.drawString(60, 24, "NeuroSight – AI MRI Analysis Report")
            canvas.drawRightString(doc.width + 60, 24, f"Page {doc.page}")
            canvas.drawCentredString((doc.width + 120) / 2, 24, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            canvas.restoreState()

        doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)

        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            raise IOError("PDF build produced an empty or missing file")

        os.replace(tmp_path, output_path)
        print(f"✅ PDF successfully created: {output_path}")
        return True

    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        traceback.print_exc()
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                print(f"Removed leftover temp file: {tmp_path}")
            except Exception:
                pass 
        raise e