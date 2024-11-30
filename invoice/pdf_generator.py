"""PDF generation utilities."""

import reportlab.lib.pagesizes
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table

(A4_WIDTH, A4_HEIGHT) = reportlab.lib.pagesizes.A4


def gen_invoice_pdf(invoice, filename_or_io):
    """Generate the invoice pdf document."""

    # pylint: disable=too-many-locals

    pdf_object = canvas.Canvas(filename_or_io)

    y_top = A4_HEIGHT - 50
    y_step = 20
    y_steps = 0

    def next_y():
        """Calculate the y position of the next line on pdf canvas."""
        nonlocal y_top, y_step, y_steps

        y = y_top - y_step * y_steps
        y_steps += 1
        return y

    def render_address(x, y, address, prefix_lines=(), suffix_lines=(), line_height=20):
        """Render an address."""
        line_count = 0
        for line in prefix_lines:
            if line:
                pdf_object.drawString(x, y - line_count * line_height, line)
                line_count += 1
        for line in [
            address.line_1,
            address.line_2,
            address.line_3,
            f"{address.postcode} {address.city}",
            address.country
        ]:
            if line:
                pdf_object.drawString(x, y - line_count * line_height, line)
                line_count += 1
        for line in suffix_lines:
            if line:
                pdf_object.drawString(x, y - line_count * line_height, line)
                line_count += 1

    x_left = 80

    # Vendor address
    render_address(x_left, y_top, invoice.vendor.address,
                   prefix_lines=[invoice.vendor.name, invoice.vendor.company_name])

    # Customer address
    render_address(A4_WIDTH - 200, y_top, invoice.customer.address, prefix_lines=[invoice.customer.full_name])

    # Title
    y_top = A4_HEIGHT - 200
    pdf_object.drawString(x_left, next_y(), "Invoice")

    # Invoice Items
    data = invoice.table_export
    table = Table(
        data=data,
        style=[
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("LEADING", (0, 0), (-1, 0), 10),
            ("ALIGNMENT", (2, 1), (6, -1), "RIGHT"),
        ]
    )
    _, table_height = table.wrapOn(pdf_object, 0, 0)
    table_y_start = next_y()
    table_y_end = table_y_start - table_height
    table.drawOn(pdf_object, x=x_left, y=table_y_end)

    # Totals
    x_right = A4_WIDTH - 280
    x_right_2 = A4_WIDTH - 195
    y_top = table_y_end
    y_steps = 1

    y = next_y()
    pdf_object.drawString(x_right, y, "Net Total:")
    pdf_object.drawAlignedString(x_right_2, y, f"{invoice.net_total:.2f}")

    y = next_y()
    pdf_object.drawString(x_right, y, "Total:")
    pdf_object.drawAlignedString(x_right_2, y, f"{invoice.total:.2f}")

    # Tax ID and bank account info
    y_top = 100
    y_steps = 0
    if invoice.vendor.tax_id:
        pdf_object.drawString(x_left, next_y(), f"Tax ID: {invoice.vendor.tax_id}")
    if invoice.vendor.bank_account:
        pdf_object.drawString(x_left, next_y(), f"IBAN: {invoice.vendor.bank_account.iban}")
        pdf_object.drawString(x_left, next_y(), f"BIC: {invoice.vendor.bank_account.bic}")

    pdf_object.showPage()
    pdf_object.save()
    return pdf_object
