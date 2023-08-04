from rest_framework.authentication import TokenAuthentication
from click.users.models import Token


class TokenOverride(TokenAuthentication):
    model = Token
