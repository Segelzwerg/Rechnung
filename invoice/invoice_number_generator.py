"""Generates invoice numbers based on custom syntax."""
from abc import ABC
from itertools import chain
from typing import List, Type

from invoice.models import Invoice


# pylint: disable=too-few-public-methods
class FormatElement(ABC):
    """Abstract class for elements in the invoice format."""

    @staticmethod
    def get(invoice: Invoice) -> str:
        """Returns the formatted part of the invoice number."""


class Year(FormatElement):
    """Invoice year format."""

    @staticmethod
    def get(invoice: Invoice) -> str:
        """Gets the year of the invoice based on the year."""
        return str(invoice.date.year)


class Counter(FormatElement):
    """Invoice counter format."""

    @staticmethod
    def get(invoice: Invoice) -> str:
        """Gets the counter of the invoice."""
        current_counter = invoice.vendor.get_next_invoice_counter()
        return str(current_counter)


class InvoiceNumberFormat:
    """Formats the invoice number."""

    def __init__(self, format_string: str):
        self._format: str = format_string

    @staticmethod
    def _convert_from_string(element: str) -> Type[FormatElement] | str:
        if element == 'year':
            return Year
        if element == 'counter':
            return Counter
        return element

    def get_elements(self) -> List[Type[FormatElement] | str]:
        """Gets all parsable elements of the invoice format."""
        element_strings = self._format.split('>')
        element_strings = list(chain.from_iterable([_.split('<') for _ in element_strings if _]))
        element_strings = [_ for _ in element_strings if _]
        return [self._convert_from_string(_) for _ in element_strings]


class InvoiceNumberGenerator:
    """Builds the number for invoices."""
    format: InvoiceNumberFormat

    def __init__(self, number_format: InvoiceNumberFormat):
        self._format: InvoiceNumberFormat = number_format

    @staticmethod
    def _compile_element(element: Type[FormatElement] | str, invoice: Invoice) -> str:
        if isinstance(element, str):
            return element
        if issubclass(element, FormatElement):
            return element.get(invoice)
        raise TypeError

    def get_invoice_number(self, invoice: Invoice) -> str:
        """Generates the invoice number."""
        format_elements = self._format.get_elements()
        return ''.join(self._compile_element(element, invoice) for element in format_elements)
