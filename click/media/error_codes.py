

class LibraryMediaErrorCode(models.TextChoices):
    NOT_FOUND = 'not_found', _('Not found')
    OUT_OF_STOCK = 'out_of_stock', _('Out of stock')


class SubscriberMediaErrorCode(models.TextChoices):
    NOT_FOUND = 'not_found', _('Not found')
    REACH_TO_LIMIT_BORROW = 'reach_to_limit_borrow', _('Reach to limit borrow')
