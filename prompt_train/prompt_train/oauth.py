from authlib.integrations.django_client import OAuth
from decouple import config

oauth = OAuth()

oauth.register(
    name="google",
    client_id=config("OAUTH_CLIENT_ID"),
    client_secret=config("OAUTH_CLIENT_SECRET"),
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    api_base_url="https://openidconnect.googleapis.com/v1/",
    client_kwargs={"scope": "openid email profile"},
)
