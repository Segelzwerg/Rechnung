from typing import List, Type, Optional

from invoice.models import Invoice


class FormatElement:
    pass

    @staticmethod
    def get(invoice: Invoice) -> str:
        pass


class Year(FormatElement):
    @staticmethod
    def get(invoice: Invoice) -> str:
        return str(invoice.date.year)


class Counter(FormatElement):
    @staticmethod
    def get(invoice: Invoice) -> str:
        current_counter = invoice.vendor.get_next_invoice_counter()
        return str(current_counter)


class InvoiceNumberFormat:
    def __init__(self, format: str):
        self._format: str = format

    def _convert_from_string(self, element: str) -> Optional[Type[FormatElement]]:
        if element == 'year':
            return Year
        if element == 'counter':
            return Counter

    def get_elements(self) -> List[Type[FormatElement]]:
        element_strings = self._format.split('>')
        element_strings = [_.lstrip('<') for _ in element_strings if _]
        return [self._convert_from_string(_) for _ in element_strings]


class InvoiceNumberGenerator:
    format: InvoiceNumberFormat

    def __init__(self, format: InvoiceNumberFormat):
        self._format: InvoiceNumberFormat = format

    def get_invoice_number(self, invoice: Invoice) -> str:
        format_elements = self._format.get_elements()
        return ''.join(_.get(invoice=invoice) for _ in format_elements)
