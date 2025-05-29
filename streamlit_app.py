import streamlit as st
import requests

# API Endpoints
BASE_URL = "https://biblegpt-be-ai.xeventechnologies.com/api/v1"
LOGIN_URL = f"{BASE_URL}/login"
GENERAL_CHATBOT_URL = f"{BASE_URL}/Gen-chatbot"
GET_ALL_NAMESPACES_URL = f"{BASE_URL}/get_all_namespaces"
BOOK_WISE_CHAT_URL = f"{BASE_URL}/book-wise-chat"

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

# For Book-wise Chat
if 'selected_book' not in st.session_state:
    st.session_state.selected_book = None
if 'book_chat_bot_id' not in st.session_state:
    st.session_state.book_chat_bot_id = ""
if 'book_conversations' not in st.session_state:
    st.session_state.book_conversations = {}

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


def get_all_namespaces():
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.get(GET_ALL_NAMESPACES_URL, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return [item['namespace'] for item in data.get('data', [])]
    return []

def general_chatbot_query(query, bot_id=0):
    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json"
    }
    payload = {
        "user_id": st.session_state.user_id,
        "query": query,
        "bot_id": bot_id  # Always include, even if 0
    }

    response = requests.post(GENERAL_CHATBOT_URL, headers=headers, json=payload)
    if response.status_code == 200:
        response_data = response.json()
        if response_data.get('data'):
            return response_data['data'].get('response'), str(response_data['data'].get('bot_id', ''))
    return None, None

def book_wise_chat_query(query, book_name, bot_id=0):
    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json"
    }
    payload = {
        "user_id": st.session_state.user_id,
        "query": query,
        "bot_id": bot_id,
        "book_name": book_name
    }

    response = requests.post(BOOK_WISE_CHAT_URL, headers=headers, json=payload)
    if response.status_code == 200:
        response_data = response.json()
        if response_data.get('data'):
            return response_data['data'].get('response'), str(response_data['data'].get('bot_id', ''))
    return None, None


def general_chat_page():
    st.title("📖 General Bible Chat")
    st.sidebar.title(f"Welcome, {st.session_state.email}")
    
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
    
    if st.sidebar.button("New General Chat"):
        st.session_state.current_bot_id = ""
        st.session_state.conversations = {}
        st.rerun()
    
    if st.session_state.current_bot_id not in st.session_state.conversations:
        st.session_state.conversations[st.session_state.current_bot_id] = []
    
    for msg in st.session_state.conversations[st.session_state.current_bot_id]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    if prompt := st.chat_input("Ask your question..."):
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, new_bot_id = general_chatbot_query(prompt, int(st.session_state.current_bot_id or 0))
                if response:
                    # Update current_bot_id if new one is returned
                    if new_bot_id and new_bot_id != st.session_state.current_bot_id:
                        old_bot_id = st.session_state.current_bot_id
                        st.session_state.current_bot_id = new_bot_id
                        if old_bot_id and old_bot_id in st.session_state.conversations:
                            st.session_state.conversations[new_bot_id] = st.session_state.conversations.pop(old_bot_id)
                        elif new_bot_id not in st.session_state.conversations:
                            st.session_state.conversations[new_bot_id] = []

                    conversation_key = st.session_state.current_bot_id
                    st.session_state.conversations[conversation_key].extend([
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": response}
                    ])

                    st.write(response)
                else:
                    st.error("Failed to get response.")

def book_wise_chat_page():
    st.title("📚 Book Wise Chat")
    st.sidebar.title("Select Bible Book")
    
    namespaces = get_all_namespaces()
    selected_book = st.sidebar.radio("Books:", namespaces)

    if selected_book != st.session_state.selected_book:
        st.session_state.selected_book = selected_book
        st.session_state.book_chat_bot_id = ""
        st.session_state.book_conversations[selected_book] = []
        st.rerun()

    if selected_book not in st.session_state.book_conversations:
        st.session_state.book_conversations[selected_book] = []

    for msg in st.session_state.book_conversations[selected_book]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input(f"Ask about {selected_book}..."):
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, new_bot_id = book_wise_chat_query(prompt, selected_book, int(st.session_state.book_chat_bot_id or 0))
                print(response, new_bot_id )
                if response:
                    # Update book_chat_bot_id if new one is returned
                    if new_bot_id and new_bot_id != st.session_state.book_chat_bot_id:
                        st.session_state.book_chat_bot_id = new_bot_id

                    st.session_state.book_conversations[selected_book].extend([
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": response}
                    ])

                    st.write(response)
                else:
                    st.error("Failed to get book-wise response.")

def login_page():
    st.title("📖 Bible GPT Login")
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if login(email, password):
                st.rerun()
            else:
                st.error("Login failed")

def main():
    st.set_page_config(page_title="Bible GPT", page_icon="📘")

    if not st.session_state.get('token'):
        login_page()
        return

    page = st.sidebar.selectbox("Select Chat Mode", ["General Chat", "Book Wise Chat"])
    
    if page == "General Chat":
        general_chat_page()
    else:
        book_wise_chat_page()

if __name__ == "__main__":
    main()
