import io
import uuid
from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.agent_builder.tools import tool
from ibm_watsonx_orchestrate.agent_builder.connections import ConnectionType
from ibm_watsonx_orchestrate.run import connections

COS_APP_ID = "cos_reports"
LINK_TTL_SECONDS = 3600


class ReportTable(BaseModel):
    heading: str = Field(description="Section heading shown above the table.")
    columns: List[str] = Field(description="Column headers.")
    rows: List[List[str]] = Field(
        description="Table rows. Every row must have the same number of cells as columns. All values are strings, already formatted (for example '92.6')."
    )
    summary: str = Field(
        default="",
        description=(
            "Optional 2-4 sentence explanation shown above the table. "
            "State what the table shows, call out the biggest variance and explain why it matters. "
            "Do not repeat numbers already in the table rows."
        ),
    )


_CHAR_MAP = {
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2212": "-",
    "\u00a0": " ", "\u202f": " ", "\u2009": " ", "\u200b": "",
}


def _safe(text: str) -> str:
    """Replace characters the built-in Helvetica font cannot draw (they render as black boxes)."""
    for src, dst in _CHAR_MAP.items():
        text = text.replace(src, dst)
    return text.encode("cp1252", errors="replace").decode("cp1252")


def _inline(text: str) -> str:
    """Escape XML, then turn **bold** and *italic* markdown into reportlab tags."""
    import re
    from xml.sax.saxutils import escape

    out = escape(_safe(text))
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)
    out = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", out)
    return out


def _build_pdf(title: str, subtitle: str, tables: List[ReportTable], commentary: str) -> bytes:
    import re
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm, title=title,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph(_inline(title), styles["Title"])]
    if subtitle:
        story.append(Paragraph(_inline(subtitle), styles["Normal"]))
    story.append(Spacer(1, 6 * mm))

    col_width = (A4[0] - 36 * mm) / 6

    for t in tables:
        story.append(Paragraph(_inline(t.heading), styles["Heading2"]))
        if t.summary:
            story.append(Paragraph(_inline(t.summary), styles["Normal"]))
            story.append(Spacer(1, 3 * mm))
        data = [[_safe(c) for c in t.columns]] + [[_safe(c) for c in r] for r in t.rows]
        n_cols = len(t.columns)
        col_widths = [col_width * 2] + [col_width] * (n_cols - 1) if n_cols > 1 else None
        table = Table(data, repeatRows=1, colWidths=col_widths)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#161616")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c6c6c6")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f4f4")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(table)
        story.append(Spacer(1, 8 * mm))

    if commentary:
        story.append(Paragraph("Executive Commentary - Draft - for review", styles["Heading2"]))
        for para in commentary.split("\n"):
            line = para.strip()
            bare = re.sub(r"[\s*_.\-:]+", " ", _safe(line)).strip().lower()
            if not line or bare in ("draft for review", "executive commentary draft for review"):
                continue
            if line[:2] in ("- ", "* "):
                line = "\u2022 " + line[2:]
            story.append(Paragraph(_inline(line).replace("\u2022", "&bull;"), styles["Normal"]))
            story.append(Spacer(1, 2 * mm))

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(18 * mm, 10 * mm, f"Generated {generated} - AI-assisted - Draft - for review")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {_doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()


@tool(
    name="publish_report_pdf",
    description=(
        "Builds a PDF management report from already-retrieved table data and commentary, uploads it to "
        "IBM Cloud Object Storage and returns a time-limited download link. Use only after the data has been "
        "retrieved from Planning Analytics."
    ),
    expected_credentials=[{"app_id": COS_APP_ID, "type": ConnectionType.KEY_VALUE}],
)
def publish_report_pdf(
    title: str,
    tables: List[ReportTable],
    commentary: str = "",
    subtitle: str = "",
) -> dict:
    """Create a PDF report, store it in Cloud Object Storage and return a download link.

    Args:
        title (str): Report title, for example '24Retail FY2024 Management Report'.
        tables (List[ReportTable]): Tables to include. Each table has a heading, columns, rows and an optional summary. The summary is a 2-4 sentence explanation shown above the table: state what the table shows, call out the biggest variance and explain its significance. Do not repeat numbers already in the rows.
        commentary (str): Full executive commentary for the end of the report. Write 1-2 paragraphs covering overall performance, key risks and outlook. Separate paragraphs with a newline. Do not include the literal phrase 'Draft - for review' — the tool adds that label automatically.
        subtitle (str): One line under the title, for example the entity, version and period.

    Returns:
        dict: download_url (valid for one hour), file_name and expires_in_minutes.
    """
    import boto3
    from botocore.config import Config

    # Normalise: the runtime may deliver each table as a plain dict instead of a ReportTable object.
    normalised = []
    for t in tables:
        if isinstance(t, dict):
            normalised.append(ReportTable(**t))
        else:
            normalised.append(t)
    tables = normalised

    for t in tables:
        for r in t.rows:
            if len(r) != len(t.columns):
                raise ValueError(
                    f"Table '{t.heading}' has a row with {len(r)} cells but {len(t.columns)} columns."
                )

    creds = connections.key_value(COS_APP_ID)
    client = boto3.client(
        "s3",
        endpoint_url=creds["COS_ENDPOINT"],
        aws_access_key_id=creds["COS_ACCESS_KEY_ID"],
        aws_secret_access_key=creds["COS_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        region_name=creds.get("COS_REGION", "us-south"),
    )
    bucket = creds["COS_BUCKET"]

    pdf_bytes = _build_pdf(title, subtitle, tables, commentary)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    key = f"reports/{stamp}-{uuid.uuid4().hex[:8]}.pdf"

    client.put_object(Bucket=bucket, Key=key, Body=pdf_bytes, ContentType="application/pdf")
    url = client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket,
            "Key": key,
            "ResponseContentType": "application/pdf",
            "ResponseContentDisposition": f'inline; filename="{key.split("/")[-1]}"',
        },
        ExpiresIn=LINK_TTL_SECONDS,
    )
    return {"download_url": url, "file_name": key, "expires_in_minutes": LINK_TTL_SECONDS // 60}
