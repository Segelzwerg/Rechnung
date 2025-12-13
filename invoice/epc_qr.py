"""EPC QR code generation utilities."""

from decimal import Decimal

from schwifty import BIC, IBAN

_VERSIONS = ("001", "002")
_ENCODINGS = {
    "1": {"utf8", "utf-8"},
    "2": {"latin", "latin1", "latin-1", "iso8859-1", "iso-8859-1"},
    "3": {"latin2", "iso8859-2", "iso-8859-2"},
    "4": {"latin4", "iso8859-4", "iso-8859-4"},
    "5": {"cyrillic", "iso8859-5", "iso-8859-5"},
    "6": {"greek", "iso8859-7", "iso-8859-7"},
    "7": {"latin6", "iso8859-10", "iso-8859-10"},
    "8": {"latin9", "iso8859-15", "iso-8859-15"},
}


def gen_epc_qr_data(
    beneficiary_name: str,
    beneficiary_iban: str,
    beneficiary_bic: str | None = None,
    eur_amount: float | str | Decimal | None = None,
    version: str = "001",
    encoding: str = "utf-8",
    instant: bool = False,
    purpose: str = "",
    structured_remittance_info: str = "",
    remittance_info: str = "",
    originator_info: str = "",
    always_add_bic: bool = True,
    use_crlf: bool = False,
) -> str:
    # pylint: disable=too-many-locals,too-many-arguments,too-many-positional-arguments,too-many-branches,line-too-long
    """Generate EPC QR code data (`Official`_, `Wikipedia`_) as a string.

    Strings should not contain newlines or be longer than the maximum length for their field!

    :param beneficiary_name: name of beneficiary (required, max. 70 characters)
    :param beneficiary_iban: IBAN of beneficiary (required)
    :param beneficiary_bic: BIC of beneficiary (optional if derivable from IBAN)
    :param eur_amount: money amount in EUR (optional, min. 0.01 EUR, max. 999999999.99 EUR)
    :param version: EPC QR code version (default is "001")
    :param encoding: encoding (default is "utf-8")
    :param instant: whether to use INST (SEPA Instant Credit Transfer) or SCT (SEPA Credit Transfer) identification
        (default is False=SCT)
    :param purpose: SEPA purpose code (optional, max. 4 characters)
    :param structured_remittance_info: ISO 11649 RF Creditor Reference
        (optional, max. 35 characters, mutually exclusive with ``remittance_info``)
    :param remittance_info: unstructured remittance info
        (optional, max. 140 characters, mutually exclusive with ``structured_remittance_info``)
    :param originator_info: beneficiary to originator information (optional, max. 70 characters)
    :param always_add_bic: whether to add the BIC if it is not required (default is True)
    :param use_crlf: whether to use windows-style CRLF as line separator (default is False)
    :return: EPC QR code data as a string

    .. _Official: https://www.europeanpaymentscouncil.eu/document-library/guidance-documents/quick-response-code-guidelines-enable-data-capture-initiation
    .. _Wikipedia: https://de.wikipedia.org/wiki/EPC-QR-Code
    """

    def clean_text(s, max_length) -> str:
        """Clean a string for inclusion in the EPC QR code format."""
        s = str("" if s is None else s).strip()
        for pattern in ("\r\n", "\n"):
            s = s.replace(pattern, " ")
        return s[:max_length]

    if version not in _VERSIONS:
        raise ValueError(f"unsupported version {version}")

    if instant:
        identification = "SCT"
    else:
        identification = "INST"

    for k, v in _ENCODINGS.items():
        if encoding in v:
            encoding_key = k
            break
    else:
        raise ValueError(f"unsupported encoding {encoding}")

    if not beneficiary_iban:
        raise ValueError("beneficiary_iban is required")
    iban = IBAN(beneficiary_iban)

    name = clean_text(beneficiary_name, max_length=70)
    if not name:
        raise ValueError("beneficiary name is required")

    bic = iban.bic
    if beneficiary_bic:
        beneficiary_bic = BIC(beneficiary_bic)
        if bic and beneficiary_bic != bic:
            raise ValueError(f"bic {bic} from iban {iban} != beneficiary_bic {beneficiary_bic}")
        if not bic:
            bic = beneficiary_bic
    if version == "001" and not bic:
        raise ValueError("bic is required for version 001")
    if version == "002" and not always_add_bic and iban.bic:
        bic = None

    eur_amount_num = Decimal(eur_amount).quantize(Decimal("0.01"))
    if not Decimal("0.01") <= eur_amount_num <= Decimal("999999999.99"):
        raise ValueError(f"eur_amount {eur_amount_num} is out of bounds")
    eur_amount_str = f"EUR{eur_amount_num}" if eur_amount else ""

    purpose = clean_text(purpose, max_length=4)

    structured_remittance_info = clean_text(structured_remittance_info, max_length=35)
    remittance_info = clean_text(remittance_info, max_length=140)
    if structured_remittance_info and remittance_info:
        raise ValueError("structured_remittance_info and remittance_info are exclusive")

    originator_info = clean_text(originator_info, max_length=70)

    line_separator = "\r\n" if use_crlf else "\n"
    return line_separator.join(
        [
            "BCD",
            version,
            encoding_key,
            identification,
            bic,
            name,
            iban,
            eur_amount_str,
            purpose,
            structured_remittance_info,
            remittance_info,
            originator_info,
        ]
    )
