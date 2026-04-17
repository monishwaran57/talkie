from app.core.config import settings



COGNITO_APP_CLIENT_ID = settings.COGNITO_APP_CLIENT_ID
COGNITO_ISSUER = f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"

import requests
from functools import lru_cache

@lru_cache()
def get_jwks():
    return requests.get(JWKS_URL).json()

from jose import jwt
from jose.exceptions import JWTError
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

http_bearer = HTTPBearer()

def get_public_key(token):
    headers = jwt.get_unverified_header(token)
    kid = headers["kid"]

    jwks = get_jwks()

    for key in jwks["keys"]:
        if key["kid"] == kid:
            return key

    raise Exception("Public key not found")


def verify_and_decode_access_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    token = credentials.credentials

    try:
        public_key = get_public_key(token)

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=COGNITO_ISSUER,
        )

        request.state.user = dict(payload)

        print("......payload in verify and decode", payload)
        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )