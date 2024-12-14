"""PDF generation utilities."""

import reportlab.lib.pagesizes
from django.utils.translation import gettext, pgettext
from reportlab.graphics.barcode.qr import QrCode
from reportlab.graphics.barcode.qrencoder import QR8bitByte
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, Paragraph
from schwifty import IBAN, BIC

from invoice import epc_qr
from invoice.models import Invoice

(A4_WIDTH, A4_HEIGHT) = reportlab.lib.pagesizes.A4


def gen_invoice_pdf(invoice, filename_or_io):
    """Generate the invoice pdf document."""

    # pylint: disable=too-many-locals

    pdf_object = canvas.Canvas(filename_or_io)
    pdf_object.setFontSize(12)

    # Labels for translation
    invoice_label = gettext('Invoice')
    invoice_number_label = pgettext('invoice number', 'Number')
    date_label = gettext('Date')
    delivery_date_label = gettext('Delivery Date')
    due_date_label = gettext('Due Date')
    net_total_label = gettext("Net Total")
    vat_label = gettext("VAT")
    total_label = gettext("Total")
    tax_id_label = gettext("Tax ID")
    iban_label = gettext("IBAN")
    bic_label = gettext("BIC")

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
            line_y = y - (i + line_offset + 1) * line_height
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
        <font size="16"><b>{invoice_label}</b></font><br/>
        <font size="12">
        {invoice_number_label}: {invoice.invoice_number}<br/>
        {date_label}: {invoice.date}
        {f'<br />{delivery_date_label}: {invoice.delivery_date}' if invoice.delivery_date else ""}
        {f'<br />{due_date_label}: {invoice.due_date}' if invoice.due_date else ""}
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
        [f'{net_total_label}: ', invoice.net_total_string],
        [f'{vat_label}: ', invoice.tax_amount_string],
        [f'{total_label}: ', invoice.total_string]
    ])

    # Tax ID and bank account info
    bottom_y = 100
    lines = []
    if invoice.vendor.tax_id:
        lines += [[f'{tax_id_label}: ', f"{invoice.vendor.tax_id}"]]
    if invoice.vendor.bank_account:
        lines += [[f'{iban_label}: ', f"{IBAN(invoice.vendor.bank_account.iban).formatted}"],
                  [f'{bic_label}: ', f"{BIC(invoice.vendor.bank_account.bic)}"]]
    if lines:
        render_lines_left_right(x_left, bottom_y, lines)

    if invoice.vendor.bank_account and invoice.currency == Invoice.Currency.EUR:
        encoding = "utf-8"
        data = epc_qr.gen_epc_qr_data(str(invoice.vendor), invoice.vendor.bank_account.iban,
                                      beneficiary_bic=invoice.vendor.bank_account.bic,
                                      eur_amount=invoice.total,
                                      remittance_info=f"{invoice_label}: {invoice.invoice_number}",
                                      encoding=encoding)
        qr_data = QR8bitByte(data.encode(encoding))
        # version must be <= 13 and error correction must be M!
        epc_qr_code = QrCode(value=[qr_data], qrVersion=None, qrLevel='M')
        w, h = epc_qr_code.wrapOn(pdf_object, A4_WIDTH - 2 * x_left, A4_HEIGHT)
        epc_qr_code.drawOn(pdf_object, A4_WIDTH - x_left - w, bottom_y - h)
        if epc_qr_code.qr.version > 13:
            raise ValueError("the epc qr code payload is limited to 331 bytes/version 13")

    pdf_object.showPage()
    pdf_object.save()
