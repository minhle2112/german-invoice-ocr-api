from xml.etree.ElementTree import Element, SubElement

from models.en16931 import GermanInvoice
from services.builders.common import add_text, code_or_default, pretty_xml, qname
from services.builders.header_builder import (
    build_document_context,
    build_exchanged_document,
    build_header_delivery,
)
from services.builders.line_builder import build_line_items
from services.builders.party_builder import build_header_agreement
from services.builders.payment_builder import build_payment_means, build_payment_terms
from services.builders.tax_builder import build_header_taxes, build_monetary_summation


def generate_cii_xml(data: GermanInvoice) -> str:
    root = Element(qname("rsm", "CrossIndustryInvoice"))

    build_document_context(root)
    build_exchanged_document(root, data.invoice)

    transaction = SubElement(root, qname("rsm", "SupplyChainTradeTransaction"))
    build_line_items(transaction, data.lines)
    build_header_agreement(transaction, data)
    build_header_delivery(transaction, data.invoice)

    header_settlement = SubElement(
        transaction,
        qname("ram", "ApplicableHeaderTradeSettlement"),
    )

    currency = code_or_default(data.invoice.currency, "EUR")

    add_text(header_settlement, "ram", "InvoiceCurrencyCode", currency)
    build_payment_means(header_settlement, data.payment)
    build_header_taxes(header_settlement, data.tax_breakdowns)
    build_payment_terms(header_settlement, data.payment_terms, data.invoice)
    build_monetary_summation(header_settlement, data.totals, currency)

    return pretty_xml(root)
