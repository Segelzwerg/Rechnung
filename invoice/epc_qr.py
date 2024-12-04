"""EPC QR code generation utilities."""

from decimal import Decimal
from typing import Optional

from schwifty import BIC, IBAN


def gen_epc_qr_data(beneficiary_name: str, beneficiary_iban: str | IBAN, beneficiary_bic: Optional[str | BIC] = None,
                    eur_amount: Optional[int | float | str | Decimal] = None,
                    version: str = "001", encoding: str = "utf-8", instant: bool = False, purpose: str = "",
                    structured_remittance_info: str = "", remittance_info: str = "", extra_info: str = "") -> str:
    # pylint: disable=too-many-locals,too-many-arguments,too-many-positional-arguments,too-many-branches,line-too-long
    """Generate EPC QR code data as str.
    Strings should not newlines or be longer than the maximum length for its field.
    Changing the encoding from "utf-8" is discouraged and will only work if both the qr code encoder and decoder support other charsets.

    .. _Wikipedia: https://de.wikipedia.org/wiki/EPC-QR-Code
    .. _EPC: https://www.europeanpaymentscouncil.eu/document-library/guidance-documents/quick-response-code-guidelines-enable-data-capture-initiation
    """

    def clean_text(s, max_length=70) -> str:
        """Clean a string for inclusion in the EPC QR code format."""
        s = str("" if s is None else s).strip()
        for pattern in ("\r\n", "\n"):
            s = s.replace(pattern, " ")
        return s[:max_length]

    if version not in ("001", "002"):
        raise ValueError(f"unsupported version {version}")

    if instant:
        identification = "SCT"
    else:
        identification = "INST"

    if encoding in ("utf8", "utf-8"):
        encoding_key = "1"
    elif encoding in ("latin", "latin1", "latin-1", "iso8859-1", "iso-8859-1"):
        encoding_key = "2"
    elif encoding in ("latin2", "iso8859-2", "iso-8859-2"):
        encoding_key = "3"
    elif encoding in ("latin4", "iso8859-4", "iso-8859-4"):
        encoding_key = "4"
    elif encoding in ("cyrillic", "iso8859-5", "iso-8859-5"):
        encoding_key = "5"
    elif encoding in ("greek", "iso8859-7", "iso-8859-7"):
        encoding_key = "6"
    elif encoding in ("latin6", "iso8859-10", "iso-8859-10"):
        encoding_key = "7"
    elif encoding in ("latin9", "iso8859-15", "iso-8859-15"):
        encoding_key = "8"
    else:
        raise ValueError(f"unsupported encoding {encoding}")

    iban = IBAN(beneficiary_iban, allow_invalid=False, validate_bban=True)
    name = clean_text(beneficiary_name)
    if not name:
        raise ValueError("beneficiary name is required")

    included_bic = iban.bic
    if beneficiary_bic:
        bic = BIC(beneficiary_bic, allow_invalid=False)
        if bic != included_bic:
            raise ValueError(f"given bic {bic} != {included_bic} from iban")
    else:
        if version == "001" and not included_bic:
            raise ValueError("bic is required for version 001")
        bic = included_bic

    eur_amount_num = Decimal(eur_amount).quantize(Decimal("0.01"))
    if not Decimal("0.01") <= eur_amount_num <= Decimal("999999999.99"):
        raise ValueError(f"eur_amount {eur_amount_num} is out of bounds")
    eur_amount_str = f"EUR{eur_amount_num}" if eur_amount else ""

    purpose = clean_text(purpose, max_length=4)

    structured_remittance_info = clean_text(structured_remittance_info, max_length=35)
    remittance_info = clean_text(remittance_info, max_length=140)
    if structured_remittance_info and remittance_info:
        raise ValueError("structured_remittance_info and remittance_info are exclusive")

    extra_info = clean_text(extra_info)

    return f"""BCD
{version}
{encoding_key}
{identification}
{bic}
{name}
{iban}
{eur_amount_str}
{purpose}
{structured_remittance_info}
{remittance_info}
{extra_info}"""
