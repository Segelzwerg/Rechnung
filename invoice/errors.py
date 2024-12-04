"""Errors of the invoice app."""


class FinalError(Exception):
    """Is raised if an instance is marked final but somebody tries to change it."""
