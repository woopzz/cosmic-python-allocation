import datetime as dt
from typing import Optional

from pydantic import ValidationError, BaseModel, PositiveInt, StrictStr

def handle_invalid_command(exc: ValidationError):
    return {
        'message': 'Invalid request data',
        'details': exc.errors(),
    }, 400


class Allocation(BaseModel):
    orderid: StrictStr
    sku: StrictStr
    qty: PositiveInt


class AddBatch(BaseModel):
    ref: StrictStr
    sku: StrictStr
    qty: PositiveInt
    eta: Optional[dt.date] = None


class ChangeBatchQuantity(BaseModel):
    batchref: StrictStr
    qty: PositiveInt
