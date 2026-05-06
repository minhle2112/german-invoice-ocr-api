from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class Address(BaseModel):
    postcode: str
    line_one: str
    city: str
    country_id: Optional[str] = None

class Contact(BaseModel):
    person_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    
class Party(BaseModel):
    name: str
    vat_id: Optional[str] = None
    address: Optional[Address] = None
    contact: Optional[Contact] = None
    
class InvoiceHeader(BaseModel):
    number: str
    issue_date: date
    delivery_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = None
    
class Payment(BaseModel):
    iban: Optional[str] = None
    bic: Optional[str] = None
    

class PaymentTerms(BaseModel):
    description: str



class InvoiceLine(BaseModel):
    id: str
    name: str
    quantity: Decimal
    unit_code: str = "C62"
    net_price: Decimal
    line_net_amount: Decimal
    tax_rate: Decimal
    
class Totals(BaseModel):
    tax_exclusive_amount: Decimal
    tax_inclusive_amount: Decimal
    tax_amount: Decimal
    payable_amount: Decimal
    

class TaxBreakdown(BaseModel):
    category_code: str = "S"
    rate: Decimal
    basis_amount: Decimal
    calculated_amount: Decimal
    

    
        
class GermanInvoice(BaseModel):
    invoice: InvoiceHeader
    seller: Party
    buyer: Party
    payment: Optional[Payment] = None
    payment_terms: Optional[PaymentTerms] = None
    totals: Totals
    lines: List[InvoiceLine]
    tax_breakdowns: List[TaxBreakdown]
