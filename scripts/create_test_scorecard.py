"""Create a minimal test scorecard PDF for CI/CD testing."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle


def create_test_scorecard_pdf(output_path: Path) -> None:
    """Create a minimal DSP scorecard PDF for testing.

    Args:
        output_path: Path where the PDF will be created
    """
    # Create document
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    # Container for elements
    elements = []
    styles = getSampleStyleSheet()

    # Title matching expected format: "DSP at STATION - Week N"
    title_text = "BWAY at DVA2 - Week 37 2025"
    title = Paragraph(title_text, styles["Title"])
    elements.append(title)

    # Subtitle
    subtitle = Paragraph("DSP Scorecard - Test Fixture", styles["Heading2"])
    elements.append(subtitle)

    # Spacer
    elements.append(Paragraph("<br/><br/>", styles["Normal"]))

    # Section header matching expected format for parser
    header = Paragraph("<b>DA Current Week Performance</b>", styles["Heading2"])
    elements.append(header)

    elements.append(Paragraph("<br/>", styles["Normal"]))

    # Sample data table
    data = [
        ["Name", "Overall Tier", "Delivered", "DCR %", "Seatbelt", "Speeding", "FICO"],
        ["Ashley Norris", "Fantastic", "250", "100.0", "100.0", "0", "850"],
        ["Brian Smith", "Great", "240", "99.5", "99.0", "0", "840"],
        ["Carol Davis", "Fantastic", "255", "100.0", "100.0", "0", "850"],
        ["David Johnson", "Great", "235", "99.0", "98.5", "1", "835"],
        ["Emma Wilson", "Fantastic", "260", "100.0", "100.0", "0", "850"],
    ]

    # Add more sample associates to meet test requirement (>= 40)
    for i in range(6, 42):
        data.append(
            [
                f"Driver {i}",
                ["Fantastic", "Great", "Good"][i % 3],
                str(230 + i),
                f"{99 + (i % 2)}.{(i * 3) % 10}",
                f"{98 + (i % 3)}.0",
                str(i % 3),
                str(820 + i % 30),
            ]
        )

    table = Table(data, colWidths=[1.2 * inch] * 7)
    table.setStyle(
        TableStyle(
            [
                # Header
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                # Body
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    elements.append(table)

    # Build PDF
    doc.build(elements)
    print(f"✅ Test scorecard PDF created at: {output_path}")


def main():
    """Main entry point."""
    # Determine output path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_path = project_root / "inputs" / "test_fixtures" / "test_scorecard.pdf"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the PDF
    create_test_scorecard_pdf(output_path)


if __name__ == "__main__":
    main()
