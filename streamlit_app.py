import streamlit as st
import requests
from datetime import datetime, timedelta

# API endpoints
BASE_URL = "https://biblegpt-be-ai.xeventechnologies.com/api/v1"
LOGIN_URL = f"{BASE_URL}/login"
GENERAL_CHATBOT_URL = f"{BASE_URL}/Gen-chatbot"

# Initialize session state
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'email' not in st.session_state:
    st.session_state.email = None
if 'current_bot_id' not in st.session_state:
    st.session_state.current_bot_id = ""
if 'conversations' not in st.session_state:
    st.session_state.conversations = {}

def login(email, password):
    payload = {"email": email, "password": password}
    response = requests.post(LOGIN_URL, json=payload)
    if response.status_code == 200:
        data = response.json()
        if data.get('succeeded'):
            st.session_state.token = data['data']['token']
            st.session_state.user_id = data['data']['user_id']
            st.session_state.email = data['data']['email']
            return True
    return False

def general_chatbot_query(query, bot_id=""):
    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json"
    }
    
    # Convert bot_id to string and handle None/empty cases
    bot_id = str(bot_id) if bot_id else ""
    
    payload = {
        "user_id": st.session_state.user_id,
        "query": query,
        "bot_id": bot_id
    }
    
    try:
        print(f"Debug - Sending payload: {payload}")  # Debug logging
        response = requests.post(GENERAL_CHATBOT_URL, headers=headers, json=payload)
        print(f"Debug - Response status: {response.status_code}")  # Debug logging
        
        if response.status_code == 200:
            response_data = response.json().get('data', {})
            if response_data:
                new_bot_id = str(response_data.get('bot_id')) if response_data.get('bot_id') else ""
                return response_data.get('response'), new_bot_id
            else:
                st.error("Empty response from server")
                return None, None
        elif response.status_code == 401:
            st.warning("Session expired. Please login again.")
            st.session_state.clear()
            st.rerun()
        elif response.status_code == 422:
            error_detail = response.json().get('detail', 'Unknown validation error')
            st.error(f"Request validation error: {error_detail}")
            print(f"Debug - Payload sent: {payload}")  # For debugging
            return None, None
        else:
            st.error(f"Server error: {response.status_code}")
            print(f"Debug - Response: {response.text}")  # For debugging
            return None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
        return None, None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        print(f"Debug - Exception: {str(e)}")  # For debugging
        return None, None

def main_app():
    st.title("Bible GPT Chat")
    st.sidebar.title(f"Welcome, {st.session_state.email}")
    
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
    
    if st.sidebar.button("New Chat"):
        st.session_state.current_bot_id = ""
        st.session_state.conversations = {}
        st.rerun()
    
    # Initialize conversation if not exists
    if st.session_state.current_bot_id not in st.session_state.conversations:
        st.session_state.conversations[st.session_state.current_bot_id] = []
    
    # Display conversation
    for msg in st.session_state.conversations[st.session_state.current_bot_id]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # Handle user input
    if prompt := st.chat_input("Ask your question..."):
        # Add user message to conversation
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Ensure we're using the correct bot_id
                current_bot_id = st.session_state.current_bot_id or ""
                response, new_bot_id = general_chatbot_query(prompt, current_bot_id)
                
                if response:
                    # Update bot_id if this was first message or if we got a new bot_id
                    if new_bot_id:
                        if current_bot_id != new_bot_id:
                            st.session_state.current_bot_id = new_bot_id
                            if current_bot_id in st.session_state.conversations:
                                st.session_state.conversations[new_bot_id] = st.session_state.conversations.pop(current_bot_id)
                            else:
                                st.session_state.conversations[new_bot_id] = []
                    
                    # Use current bot_id for storing messages
                    conversation_key = st.session_state.current_bot_id
                    
                    # Add messages to conversation
                    st.session_state.conversations[conversation_key].append({
                        "role": "user",
                        "content": prompt
                    })
                    st.session_state.conversations[conversation_key].append({
                        "role": "assistant",
                        "content": response
                    })
                    st.write(response)
                else:
                    st.error("Failed to get response. Please try reloading the page or logging in again.")

def login_page():
    st.title("Bible GPT Login")
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if login(email, password):
                st.rerun()
            else:
                st.error("Login failed")

def main():
    st.set_page_config(page_title="Bible GPT", page_icon="📖")
    if st.session_state.get('token'):
        main_app()
    else:
        login_page()

if __name__ == "__main__":
    main()