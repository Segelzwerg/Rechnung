"""Errors of the invoice app."""


class FinalError(Exception):
    """Is raised if an instance is marked final but somebody tries to change it."""


class IncompliantWarning(Warning):
    """IS raised if the invoice is legally not compliant."""
