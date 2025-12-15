from datetime import datetime
from uuid import UUID
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse
from app.schemas.user import UserResponse
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> UserResponse:
    """
    Dependency to get the current user from the JWT token without a database lookup.
    This function supports two types of payloads:
      - A full payload as a dict containing user info.
      - A minimal payload, either as a dict with only a 'sub' key or directly as a UUID.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = User.verify_token(token)
    if token_data is None:
        raise credentials_exception

    try:
        # If the token data is a dictionary:
        if isinstance(token_data, dict):
            # If the payload contains a full set of user fields, use them directly.
            if "username" in token_data:
                return UserResponse(**token_data)
            # Otherwise, assume it is a minimal payload with only the 'sub' key.
            elif "sub" in token_data:
                return UserResponse(
                    id=token_data["sub"],
                    username="unknown",
                    email="unknown@example.com",
                    first_name="Unknown",
                    last_name="User",
                    is_active=True,
                    is_verified=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            else:
                raise credentials_exception

        # If the token data is directly a UUID (minimal payload):
        elif isinstance(token_data, UUID):
            return UserResponse(
                id=token_data,
                username="unknown",
                email="unknown@example.com",
                first_name="Unknown",
                last_name="User",
                is_active=True,
                is_verified=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        else:
            raise credentials_exception

    except Exception:
        raise credentials_exception

def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Dependency to ensure that the current user is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_web_user(request: Request) -> UserResponse:
    """
    Dependency for web routes (HTML pages) that require authentication.
    
    This checks for a JWT token in the Authorization header or cookies.
    If not authenticated, it triggers a redirect to the login page.
    
    This is designed for server-rendered HTML pages, not API endpoints.
    
    Args:
        request: The FastAPI Request object
        
    Returns:
        UserResponse: The authenticated user's data
        
    Raises:
        HTTPException: With redirect information to /login if not authenticated
    """
    # Try to get token from Authorization header first (for API compatibility)
    auth_header = request.headers.get("Authorization")
    token = None
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
    
    # If no token in header, try to get from cookie (for browser sessions)
    if not token:
        token = request.cookies.get("access_token")
    
    # If still no token, we need to redirect to login
    # Since we can't return a Response from a dependency, we raise HTTPException
    # and let the route handler catch it or use an exception handler
    if not token:
        # Raise a special exception that can be caught and converted to redirect
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - please login",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify the token
    token_data = User.verify_token(token)
    if token_data is None:
        # Invalid token - need to redirect to login
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token - please login",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Parse token data into UserResponse
    try:
        if isinstance(token_data, dict):
            if "username" in token_data:
                user = UserResponse(**token_data)
            elif "sub" in token_data:
                user = UserResponse(
                    id=token_data["sub"],
                    username="unknown",
                    email="unknown@example.com",
                    first_name="Unknown",
                    last_name="User",
                    is_active=True,
                    is_verified=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            else:
                raise ValueError("Invalid token structure")
        elif isinstance(token_data, UUID):
            user = UserResponse(
                id=token_data,
                username="unknown",
                email="unknown@example.com",
                first_name="Unknown",
                last_name="User",
                is_active=True,
                is_verified=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        else:
            raise ValueError("Invalid token type")
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user - please contact support",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception:
        # Any error parsing token - need to redirect to login
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error - please login",
            headers={"WWW-Authenticate": "Bearer"}
        )
