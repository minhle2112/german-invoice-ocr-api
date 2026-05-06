from models.en16931 import GermanInvoice


def validate_invoice(data: GermanInvoice):
    errors = []

    line_sum = sum(line.line_net_amount for line in data.lines)

    if line_sum != data.totals.tax_exclusive_amount:
        errors.append(
            "Sum of line_net_amount must equal tax_exclusive_amount"
        )

    tax_sum = sum(tax.calculated_amount for tax in data.tax_breakdowns)

    if tax_sum != data.totals.tax_amount:
        errors.append(
            "Sum of tax_breakdowns.calculated_amount must equal tax_amount"
        )

    calculated_gross = (
        data.totals.tax_exclusive_amount
        + data.totals.tax_amount
    )

    if calculated_gross != data.totals.tax_inclusive_amount:
        errors.append(
            "tax_exclusive_amount + tax_amount must equal tax_inclusive_amount"
        )

    if data.totals.payable_amount != data.totals.tax_inclusive_amount:
        errors.append(
            "payable_amount must equal tax_inclusive_amount for invoices without prepaid amount"
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }