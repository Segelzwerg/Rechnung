"""PDF generation utilities."""

import reportlab.lib.pagesizes
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table

(A4_WIDTH, A4_HEIGHT) = reportlab.lib.pagesizes.A4


def gen_invoice_pdf(invoice, filename_or_io):
    """Generate the invoice pdf document."""
    pdf_object = canvas.Canvas(filename_or_io)

    y_top = 800
    y_step = 20
    y_steps = 0

    def next_y():
        """Calculate the y position of the next line on pdf canvas."""
        nonlocal y_steps

        y = y_top - y_step * y_steps
        y_steps += 1
        return y

    x_left = 100

    # Vendor address
    pdf_object.drawString(x_left, next_y(), invoice.vendor.name)
    if invoice.vendor.company_name:
        pdf_object.drawString(x_left, next_y(), invoice.vendor.company_name)
    for line in [invoice.vendor.address.line_1, invoice.vendor.address.line_2, invoice.vendor.address.line_3]:
        if line:
            pdf_object.drawString(x_left, next_y(), line)
    pdf_object.drawString(x_left, next_y(), f'{invoice.vendor.address.postcode} {invoice.vendor.address.city}')
    pdf_object.drawString(x_left, next_y(), invoice.vendor.address.country)

    # Title
    next_y()
    pdf_object.drawString(x_left, next_y(), "Rechnung")

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
    table.drawOn(pdf_object, x=x_left, y=table_y_start - table_height)

    # Totals
    x_right = A4_WIDTH - 280
    x_right_2 = A4_WIDTH - 195
    y_top = table_y_start - table_height
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
