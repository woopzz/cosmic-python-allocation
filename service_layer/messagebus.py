from domain import events
from adapters import email

def handle(event: events.Event):
    for hander in HANDLERS[type(event)]:
        hander(event)

def send_out_of_stock_notification(event: events.OutOfStock):
    email.send_mail(f'Out of stock for {event.sku}')

HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notification],
}
