@router.post("/login", 
    summary="User Authentication",
    description="Authenticate a user and receive a JWT token. Both username and password are required.",
    responses={
        200: {"description": "Login successful, returns access token and user details"},
        401: {"description": "Invalid username or password"},
    },
    tags=["Authentication"]
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint.
    
    **Request Parameters:**
    - `username`: User's username (1-50 characters)
    - `password`: User's password (1-128 characters)
    
    **Response:**
    - `access_token`: JWT token for authenticated requests
    - `token_type`: Always "bearer"
    - `role`: User's role (admin/operator)
    - `shop_id`: Assigned shop (null for admins)
    - `must_reset_password`: Password reset flag
    """
    user = db.query(User).filter(User.username == payload.username.strip()).first()
    if not user or not verify_password(payload.password, str(user.hashed_password)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
        "shop_id": user.shop_id,
        "must_reset_password": user.must_reset_password,
    }


@router.get("/me", 
    summary="Get Current User",
    description="Retrieve authenticated user's profile information.",
    responses={
        200: {"description": "User profile retrieved successfully"},
        401: {"description": "Invalid or expired token"},
    },
    tags=["Authentication"]
)
def me(user: User = Depends(get_current_user)):
    """Get currently authenticated user's information."""
    return {"id": user.id, "username": user.username, "role": user.role, "shop_id": user.shop_id}


@router.post("/logout", 
    summary="User Logout",
    description="Revoke the current JWT token to prevent reuse even before natural expiration.",
    responses={
        200: {"description": "Logout successful"},
        401: {"description": "Invalid or expired token"},
    },
    tags=["Authentication"]
)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Revoke the current token so it cannot be reused even before it naturally expires."""
    revoke_token(credentials, db)
    return {"message": "Logged out successfully."}