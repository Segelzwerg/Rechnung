"""Generates invoice numbers based on custom syntax."""

# pylint: disable=used-before-assignment
# false positive caused by hiding Invoice import behind type-checking check

from abc import ABC, abstractmethod
from itertools import chain
from typing import TYPE_CHECKING

from invoice.constants import DEFAULT_INVOICE_NUMBER_COUNTER, DEFAULT_INVOICE_NUMBER_ZERO_PADDING

if TYPE_CHECKING:
    from invoice.models import Invoice


class FormatElement(ABC):
    """Abstract class for elements in the invoice format."""

    @abstractmethod
    def get(self, invoice: Invoice) -> str:
        """Return the formatted part of the invoice number, may have side effects."""

    @abstractmethod
    def preview(self, invoice: Invoice) -> str:
        """Preview the formatted part of the invoice number without side effects."""


class Year(FormatElement):
    """Invoice year format."""

    def get(self, invoice: Invoice) -> str:
        """Get the year of the invoice."""
        return str(invoice.date.year).zfill(4)

    def preview(self, invoice: Invoice) -> str:
        """Preview the year of the invoice."""
        return self.get(invoice)


class Month(FormatElement):
    """Invoice month format."""

    def get(self, invoice: Invoice) -> str:
        """Get the month of the invoice."""
        return str(invoice.date.month).zfill(2)

    def preview(self, invoice: Invoice) -> str:
        """Preview the month of the invoice."""
        return self.get(invoice)


class Day(FormatElement):
    """Invoice day format."""

    def get(self, invoice: Invoice) -> str:
        """Get the day of the invoice."""
        return str(invoice.date.day).zfill(2)

    def preview(self, invoice: Invoice) -> str:
        """Preview the day of the invoice."""
        return self.get(invoice)


class Customer(FormatElement):
    """Invoice customer format."""

    def get(self, invoice: Invoice) -> str:
        """Get the customer id of the invoice."""
        # TODO: get a short, readable customer id
        return str(invoice.customer.id)

    def preview(self, invoice: Invoice) -> str:
        """Preview the customer id of the invoice."""
        return self.get(invoice)


class Vendor(FormatElement):
    """Invoice vendor format."""

    def get(self, invoice: Invoice) -> str:
        """Get the vendor id of the invoice."""
        # TODO: get a short, readable vendor id
        return str(invoice.vendor.id)

    def preview(self, invoice: Invoice) -> str:
        """Preview the vendor id of the invoice."""
        return self.get(invoice)


class Counter(FormatElement):
    """Invoice counter format."""

    def __init__(self, counter_type: str, index: int, zero_padding: int):
        """Create an invoice counter format given its index in the format string."""
        self.counter_type = counter_type
        self.index = index
        self.zero_padding = zero_padding

    def _format_counter(self, counter: int) -> str:
        if counter <= 0:
            raise ValueError(f"{self.counter_type} counter {counter} must be positive")
        return str(counter).zfill(self.zero_padding)

    def get(self, invoice: Invoice) -> str:
        """Get the counter of the invoice."""
        if self.counter_type == "vendor":
            counter = invoice.vendor.get_next_invoice_counter()
        elif self.counter_type == "customer":
            counter = invoice.customer.get_next_invoice_counter()
        else:
            raise NotImplementedError
        return self._format_counter(counter)

    def preview(self, invoice: Invoice) -> str:
        """Preview the invoice counter."""
        if self.counter_type == "vendor":
            counter_base = invoice.vendor.invoice_counter
        elif self.counter_type == "customer":
            counter_base = invoice.customer.invoice_counter
        else:
            raise NotImplementedError
        return self._format_counter(counter_base + 1 + self.index)


class Literal(FormatElement):
    """Literal string for invoice number format."""

    def __init__(self, literal: str):
        """Create an invoice number format given a literal string."""
        self._literal: str = str(literal)

    def get(self, _invoice: Invoice) -> str:
        """Get the counter of the invoice."""
        return self._literal

    def preview(self, invoice: Invoice) -> str:
        """Preview the invoice counter."""
        return self.get(invoice)


class InvoiceNumberFormat:
    """Formats the invoice number."""

    def __init__(self, format_string: str):
        """Create an invoice number format given a format string."""
        self._counter_indices: dict[str, int] = {}
        self._format: list[FormatElement] = self._compile(format_string)

    def _convert_from_string(self, element: str) -> FormatElement:
        element_type, *args = element.split(":")

        simple_elements = {"year": Year, "month": Month, "day": Day, "customer": Customer, "vendor": Vendor}
        if element_type in simple_elements:
            return simple_elements[element_type]()

        if element_type == "counter":
            counter_type_arg = args[0] if args else DEFAULT_INVOICE_NUMBER_COUNTER
            if counter_type_arg in {"vendor", "customer"}:
                counter_type = counter_type_arg
            else:
                raise ValueError(f"unknown counter type {counter_type_arg}")

            zero_padding_arg = args[1] if args and len(args) >= 2 else None  # noqa: PLR2004, magic constant for length 2
            try:
                zero_padding = int(zero_padding_arg)
            except (TypeError, ValueError):
                zero_padding = DEFAULT_INVOICE_NUMBER_ZERO_PADDING

            counter_index = self._counter_indices.get(counter_type, 0)
            self._counter_indices[counter_type] = counter_index + 1
            return Counter(counter_type, counter_index, zero_padding)
        return Literal(element)

    def _compile(self, format_string: str) -> list[FormatElement]:
        """Get all parsable elements of the invoice format."""
        element_strings = format_string.split(">")
        element_strings = list(chain.from_iterable([_.split("<") for _ in element_strings if _]))
        element_strings = [_ for _ in element_strings if _]
        return [self._convert_from_string(_) for _ in element_strings]

    def get_invoice_number(self, invoice: Invoice) -> str:
        """Generate the invoice number."""
        return "".join(f.get(invoice) for f in self._format)

    def preview_invoice_number(self, invoice: Invoice) -> str:
        """Preview the invoice number."""
        return "".join(f.preview(invoice) for f in self._format)
