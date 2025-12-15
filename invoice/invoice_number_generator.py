"""Generates invoice numbers based on custom syntax."""

# pylint: disable=used-before-assignment
# false positive caused by hiding Invoice import behind type-checking check

from abc import ABC, abstractmethod
from itertools import chain
from typing import TYPE_CHECKING

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
        return str(invoice.date.year)

    def preview(self, invoice: Invoice) -> str:
        """Preview the year of the invoice."""
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


class Counter(FormatElement):
    """Invoice counter format."""

    def __init__(self, counter_type: str, index: int):
        """Create an invoice counter format given its index in the format string."""
        self.counter_type = counter_type
        self.index = index

    def get(self, invoice: Invoice) -> str:
        """Get the counter of the invoice."""
        if self.counter_type == "vendor":
            return str(invoice.vendor.get_next_invoice_counter())
        if self.counter_type == "customer":
            return str(invoice.customer.get_next_invoice_counter())
        raise NotImplementedError

    def preview(self, invoice: Invoice) -> str:
        """Preview the invoice counter."""
        if self.counter_type == "vendor":
            return str(invoice.vendor.invoice_counter + 1 + self.index)
        if self.counter_type == "customer":
            return str(invoice.customer.invoice_counter + 1 + self.index)
        raise NotImplementedError


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
        element_type, *args = element.split(":", maxsplit=1)
        arg = args[0] if args else None

        if element_type == "year":
            return Year()
        if element_type == "counter":
            if not arg or arg == "vendor":
                counter_type = "vendor"
            elif arg == "customer":
                counter_type = "customer"
            else:
                raise ValueError(f"unknown counter type {arg}")

            counter_index = self._counter_indices.get(counter_type, 0)
            self._counter_indices[counter_type] = counter_index + 1
            return Counter(counter_type, counter_index)
        if element == "customer":
            return Customer()
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
