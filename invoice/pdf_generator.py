import reportlab.lib.pagesizes
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table

(A4_WIDTH, A4_HEIGHT) = reportlab.lib.pagesizes.A4


def get_y_position(y_print_start, y_step, y_steps):
    """Calculate the y position of the next line on pdf canvas."""
    return y_print_start - y_step * y_steps


def gen_invoice_pdf(invoice, filename_or_io):
    pdf_object = canvas.Canvas(filename_or_io)
    y_print_start = 800
    y_step = 20
    y_steps = 0
    pdf_object.drawString(100, get_y_position(y_print_start, y_step, y_steps), invoice.vendor.name)
    y_steps += 1
    if invoice.vendor.company_name:
        pdf_object.drawString(100, get_y_position(y_print_start, y_step, y_steps),
                              invoice.vendor.company_name)
        y_steps += 1
    pdf_object.drawString(100, get_y_position(y_print_start, y_step, y_steps),
                          invoice.vendor.address.line_1)
    y_steps += 1
    if invoice.vendor.address.line_2:
        pdf_object.drawString(100, get_y_position(y_print_start, y_step, y_steps),
                              invoice.vendor.address.line_2)
        y_steps += 1
    if invoice.vendor.address.line_3:
        pdf_object.drawString(100, get_y_position(y_print_start, y_step, y_steps),
                              invoice.vendor.address.line_3)
        y_steps += 1
    pdf_object.drawString(100, get_y_position(y_print_start, y_step, y_steps),
                          f'{invoice.vendor.address.postcode} {invoice.vendor.address.city}')
    y_steps += 1
    pdf_object.drawString(100, get_y_position(y_print_start, y_step, y_steps),
                          invoice.vendor.address.country)
    y_steps += 1
    pdf_object.drawString(100, get_y_position(y_print_start, y_step, y_steps), 'Rechnung')
    y_steps += 1

    data = invoice.table_export
    table = Table(
        data=data,
        style=[
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEADING', (0, 0), (-1, 0), 10),
            ('ALIGNMENT', (2, 1), (6, -1), "RIGHT"),
        ]
    )
    _, table_height = table.wrapOn(pdf_object, 0, 0)

    table_y_start = get_y_position(y_print_start, y_step, y_steps)
    table.drawOn(pdf_object, x=100, y=table_y_start - table_height)

    pdf_object.drawString(A4_WIDTH - 280, table_y_start - table_height - y_step, 'Net Total:')
    pdf_object.drawAlignedString(A4_WIDTH - 195, table_y_start - table_height - y_step, f'{invoice.net_total:.2f}')

    pdf_object.drawString(A4_WIDTH - 280, table_y_start - table_height - y_step * 2, 'Total:')
    pdf_object.drawAlignedString(A4_WIDTH - 195, table_y_start - table_height - y_step * 2, f'{invoice.total:.2f}')

    if invoice.vendor.tax_id:
        pdf_object.drawString(100, 100, f'Tax ID: {invoice.vendor.tax_id}')
    if invoice.vendor.bank_account:
        pdf_object.drawString(100, 80, f'IBAN: {invoice.vendor.bank_account.iban}')
        pdf_object.drawString(100, 60, f'BIC: {invoice.vendor.bank_account.bic}')

    pdf_object.showPage()
    pdf_object.save()
    return pdf_object
