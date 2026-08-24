def stream_api_request(method: str, endpoint: str, payload: dict = None) -> any:
    """
    Make streaming API request (for chat responses).
    
    Returns response object that can be iterated for streaming.
    """
    token = st.session_state.get("access_token")
    if not token:
        st.error("Not authenticated")
        return None
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    url = f"{base_url}{endpoint}"
    
    try:
        if method == "POST":
            response = requests.post(url, json=payload, headers=headers, stream=True)
        elif method == "GET":
            response = requests.get(url, headers=headers, stream=True)
        else:
            return None
        
        if response.status_code == 401:
            st.error("Session expired. Please log in again.")
            st.session_state.authenticated = False
            st.rerun()
            return None
        
        response.raise_for_status()
        return response
    
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None