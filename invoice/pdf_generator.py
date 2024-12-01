"""PDF generation utilities."""

import reportlab.lib.pagesizes
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, Paragraph
from schwifty import IBAN, BIC

(A4_WIDTH, A4_HEIGHT) = reportlab.lib.pagesizes.A4


def gen_invoice_pdf(invoice, filename_or_io):
    """Generate the invoice pdf document."""

    # pylint: disable=too-many-locals,too-many-arguments,too-many-positional-arguments

    pdf_object = canvas.Canvas(filename_or_io)
    pdf_object.setFontSize(12)

    def render_lines(x, y, lines):
        """Render lines."""
        text = '<br/>'.join(lines)
        p = Paragraph(text)
        _, h = p.wrapOn(pdf_object, A4_WIDTH, A4_HEIGHT)
        y_end = y - h
        p.drawOn(pdf_object, x, y_end)
        return y_end

    def render_address(x, y, address, prefix_lines=(), suffix_lines=()):
        """Render an address."""
        all_lines = [line for line in prefix_lines if line] + [line for line in [
            address.line_1,
            address.line_2,
            address.line_3,
            f"{address.postcode} {address.city}",
            address.country
        ] if line] + [line for line in suffix_lines if line]
        return render_lines(x, y, all_lines)

    def render_lines_left_right(x, y, lines, line_offset=0, line_height=16):
        """Render two-part lines left- and right-aligned.
        Expects lines to be a tuple with two elements.
        The first element will be left-aligned, the second element will be right-aligned."""
        max_width = (max(map(pdf_object.stringWidth, [row[0] for row in lines])) +
                     max(map(pdf_object.stringWidth, [row[1] for row in lines])))
        if x < 0:
            x = -x - max_width
        for i, (text_l, text_r) in enumerate(lines):
            line_y = y - (i + line_offset) * line_height
            pdf_object.drawString(x, line_y, text_l)
            pdf_object.drawRightString(x + max_width, line_y, text_r)

    y_top = A4_HEIGHT - 50
    x_left = 80

    # Vendor address
    render_address(x_left, y_top, invoice.vendor.address,
                   prefix_lines=[invoice.vendor.name, invoice.vendor.company_name])

    # Customer address
    render_address(A4_WIDTH - 200, y_top, invoice.customer.address, prefix_lines=[invoice.customer.full_name])

    # Title, number, date
    title = Paragraph(f"""
        <font size="16"><b>Invoice</b></font><br/>
        <font size="12">
        Number: {invoice.invoice_number}<br/>
        Date: {invoice.date}
        {f'<br />Due Date: {invoice.due_date}' if invoice.due_date else ""}
        </font>
""")
    _, h = title.wrapOn(pdf_object, A4_WIDTH, A4_HEIGHT)
    y_title_end = A4_HEIGHT - 150 - h
    title.drawOn(pdf_object, x_left, y_title_end)

    # Invoice Items
    data = invoice.table_export
    table = Table(
        data=[[Paragraph(f"<b>{col}</b>") if i == 0 else str(col) for col in row] for i, row in enumerate(data)],
        style=[
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("LEADING", (0, 0), (-1, 0), 10),
            ("ALIGNMENT", (2, 1), (6, -1), "RIGHT"),
        ]
    )
    _, table_height = table.wrapOn(pdf_object, A4_WIDTH - 2 * x_left, A4_HEIGHT)
    table_y_start = y_title_end - 20
    table_y_end = table_y_start - table_height
    table.drawOn(pdf_object, x_left, table_y_end)

    # Totals
    render_lines_left_right(-(A4_WIDTH - x_left), table_y_end, [
        ["Net Total: ", invoice.net_total_string],
        ["Total: ", invoice.total_string]
    ], line_offset=1)

    # Tax ID and bank account info
    lines = []
    if invoice.vendor.tax_id:
        lines += [["Tax ID: ", f"{invoice.vendor.tax_id}"]]
    if invoice.vendor.bank_account:
        lines += [["IBAN: ", f"{IBAN(invoice.vendor.bank_account.iban).formatted}"],
                  ["BIC: ", f"{BIC(invoice.vendor.bank_account.bic)}"]]
    if lines:
        render_lines_left_right(x_left, 100, lines)

    pdf_object.showPage()
    pdf_object.save()
