from datetime import datetime
from decimal import Decimal

import fitz
from lxml import etree

from models.en16931 import (
    Address,
    GermanInvoice,
    InvoiceHeader,
    InvoiceLine,
    Party,
    Payment,
    PaymentTerms,
    TaxBreakdown,
    Totals,
)
from services.builders.common import NS


PDF_SIGNATURE = b"%PDF"


def extract_cii_xml_from_file(contents: bytes, filename: str | None = None) -> str:
    if _looks_like_pdf(contents, filename):
        return extract_cii_xml_from_pdf(contents)

    try:
        return contents.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Uploaded file is not valid UTF-8 XML") from exc


def extract_cii_xml_from_pdf(contents: bytes) -> str:
    try:
        doc = fitz.open(stream=contents, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Invalid PDF file: {exc}") from exc

    xml_candidates = []

    for index in range(doc.embfile_count()):
        info = doc.embfile_info(index)
        attachment_name = (info.get("filename") or info.get("ufilename") or "").lower()

        if not attachment_name.endswith(".xml"):
            continue

        try:
            xml_bytes = doc.embfile_get(index)
            xml = xml_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            continue

        if "CrossIndustryInvoice" in xml:
            return xml

        xml_candidates.append(xml)

    if xml_candidates:
        return xml_candidates[0]

    raise ValueError(
        "No embedded CII XML attachment found in PDF. "
        "Expected a ZUGFeRD/Factur-X PDF with an XML attachment."
    )


def _looks_like_pdf(contents: bytes, filename: str | None) -> bool:
    return (
        bool(filename and filename.lower().endswith(".pdf"))
        or contents.lstrip().startswith(PDF_SIGNATURE)
    )


def _text(node, xpath: str) -> str | None:
    result = node.xpath(xpath, namespaces=NS)
    if not result:
        return None

    value = result[0].text
    return value.strip() if value else None


def _required_text(node, xpath: str, field_name: str) -> str:
    value = _text(node, xpath)
    if value is None:
        raise ValueError(f"Missing required XML field: {field_name}")
    return value


def _decimal(node, xpath: str, field_name: str) -> Decimal:
    return Decimal(_required_text(node, xpath, field_name))


def _date_from_cii(node, xpath: str, field_name: str):
    value = _required_text(node, xpath, field_name)
    return datetime.strptime(value, "%Y%m%d").date()


def _optional_date_from_cii(node, xpath: str):
    value = _text(node, xpath)
    if value is None:
        return None
    return datetime.strptime(value, "%Y%m%d").date()


def _parse_address(party_node) -> Address | None:
    address_node = party_node.find("ram:PostalTradeAddress", namespaces=NS)
    if address_node is None:
        return None

    return Address(
        postcode=_required_text(address_node, "ram:PostcodeCode", "address.postcode"),
        line_one=_required_text(address_node, "ram:LineOne", "address.line_one"),
        city=_required_text(address_node, "ram:CityName", "address.city"),
        country_id=_text(address_node, "ram:CountryID"),
    )


def _parse_party(root, xpath: str, field_name: str) -> Party:
    party_node = root.find(xpath, namespaces=NS)
    if party_node is None:
        raise ValueError(f"Missing required XML field: {field_name}")

    return Party(
        name=_required_text(party_node, "ram:Name", f"{field_name}.name"),
        vat_id=_text(party_node, "ram:SpecifiedTaxRegistration/ram:ID"),
        address=_parse_address(party_node),
    )


def _parse_payment(root) -> Payment | None:
    payment_node = root.find(
        ".//ram:ApplicableHeaderTradeSettlement/"
        "ram:SpecifiedTradeSettlementPaymentMeans",
        namespaces=NS,
    )
    if payment_node is None:
        return None

    iban = _text(payment_node, "ram:PayeePartyCreditorFinancialAccount/ram:IBANID")
    bic = _text(payment_node, "ram:PayeeSpecifiedCreditorFinancialInstitution/ram:BICID")

    if not iban and not bic:
        return None

    return Payment(iban=iban, bic=bic)


def _parse_payment_terms(root) -> PaymentTerms | None:
    terms_node = root.find(
        ".//ram:ApplicableHeaderTradeSettlement/ram:SpecifiedTradePaymentTerms",
        namespaces=NS,
    )
    if terms_node is None:
        return None

    description = _text(terms_node, "ram:Description")
    if not description:
        return None

    return PaymentTerms(description=description)


def _parse_lines(root) -> list[InvoiceLine]:
    lines = []

    for line_node in root.findall(
        ".//ram:IncludedSupplyChainTradeLineItem",
        namespaces=NS,
    ):
        quantity_node = line_node.find(
            "ram:SpecifiedLineTradeDelivery/ram:BilledQuantity",
            namespaces=NS,
        )
        unit_code = quantity_node.get("unitCode", "C62") if quantity_node is not None else "C62"

        lines.append(
            InvoiceLine(
                id=_required_text(
                    line_node,
                    "ram:AssociatedDocumentLineDocument/ram:LineID",
                    "line.id",
                ),
                name=_required_text(line_node, "ram:SpecifiedTradeProduct/ram:Name", "line.name"),
                quantity=_decimal(
                    line_node,
                    "ram:SpecifiedLineTradeDelivery/ram:BilledQuantity",
                    "line.quantity",
                ),
                unit_code=unit_code,
                net_price=_decimal(
                    line_node,
                    "ram:SpecifiedLineTradeAgreement/"
                    "ram:NetPriceProductTradePrice/ram:ChargeAmount",
                    "line.net_price",
                ),
                line_net_amount=_decimal(
                    line_node,
                    "ram:SpecifiedLineTradeSettlement/"
                    "ram:SpecifiedTradeSettlementLineMonetarySummation/"
                    "ram:LineTotalAmount",
                    "line.line_net_amount",
                ),
                tax_rate=_decimal(
                    line_node,
                    "ram:SpecifiedLineTradeSettlement/"
                    "ram:ApplicableTradeTax/ram:RateApplicablePercent",
                    "line.tax_rate",
                ),
            )
        )

    return lines


def _parse_tax_breakdowns(root) -> list[TaxBreakdown]:
    tax_breakdowns = []

    for tax_node in root.findall(
        ".//ram:ApplicableHeaderTradeSettlement/ram:ApplicableTradeTax",
        namespaces=NS,
    ):
        tax_breakdowns.append(
            TaxBreakdown(
                category_code=_text(tax_node, "ram:CategoryCode") or "S",
                rate=_decimal(tax_node, "ram:RateApplicablePercent", "tax.rate"),
                basis_amount=_decimal(tax_node, "ram:BasisAmount", "tax.basis_amount"),
                calculated_amount=_decimal(
                    tax_node,
                    "ram:CalculatedAmount",
                    "tax.calculated_amount",
                ),
            )
        )

    return tax_breakdowns


def _parse_totals(root) -> Totals:
    monetary_xpath = ".//ram:SpecifiedTradeSettlementHeaderMonetarySummation"
    return Totals(
        tax_exclusive_amount=_decimal(
            root,
            f"{monetary_xpath}/ram:TaxBasisTotalAmount",
            "totals.tax_exclusive_amount",
        ),
        tax_inclusive_amount=_decimal(
            root,
            f"{monetary_xpath}/ram:GrandTotalAmount",
            "totals.tax_inclusive_amount",
        ),
        tax_amount=_decimal(root, f"{monetary_xpath}/ram:TaxTotalAmount", "totals.tax_amount"),
        payable_amount=_decimal(
            root,
            f"{monetary_xpath}/ram:DuePayableAmount",
            "totals.payable_amount",
        ),
    )


def parse_cii_xml(xml_string: str) -> GermanInvoice:
    try:
        root = etree.fromstring(xml_string.encode("utf-8"))
    except etree.XMLSyntaxError as exc:
        raise ValueError(f"Invalid XML: {exc}") from exc

    invoice = InvoiceHeader(
        number=_required_text(root, "rsm:ExchangedDocument/ram:ID", "invoice.number"),
        issue_date=_date_from_cii(
            root,
            "rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString",
            "invoice.issue_date",
        ),
        delivery_date=_optional_date_from_cii(
            root,
            ".//ram:ApplicableHeaderTradeDelivery/"
            "ram:ActualDeliverySupplyChainEvent/"
            "ram:OccurrenceDateTime/udt:DateTimeString",
        ),
        due_date=_optional_date_from_cii(
            root,
            ".//ram:SpecifiedTradePaymentTerms/ram:DueDateDateTime/udt:DateTimeString",
        ),
        currency=_text(root, ".//ram:ApplicableHeaderTradeSettlement/ram:InvoiceCurrencyCode"),
    )

    return GermanInvoice(
        invoice=invoice,
        seller=_parse_party(
            root,
            ".//ram:ApplicableHeaderTradeAgreement/ram:SellerTradeParty",
            "seller",
        ),
        buyer=_parse_party(
            root,
            ".//ram:ApplicableHeaderTradeAgreement/ram:BuyerTradeParty",
            "buyer",
        ),
        payment=_parse_payment(root),
        payment_terms=_parse_payment_terms(root),
        totals=_parse_totals(root),
        lines=_parse_lines(root),
        tax_breakdowns=_parse_tax_breakdowns(root),
    )
