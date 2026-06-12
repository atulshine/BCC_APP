import streamlit as st
from supabase import create_client, Client
import time

# --- 1. SUPABASE DATABASE CONNECTION ---
# Your unique project reference ID extracted from your key: anvdrjpyluzopzsgvirh
SUPABASE_URL = "https://anvdrjpyluzopzsgvirh.supabase.co"
# Your actual Supabase Anon Public Key
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFudmRyanB5bHV6b3B6c2d2aXJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEyNTk4MTgsImV4cCI6MjA5NjgzNTgxOH0.F2YHgCaCSfYOej0SZdRHrRjvImAIfBElt71KMNG59YA"

@st.cache_resource
def init_supabase() -> Client:
    # Correctly passing the credential variables into the client initialization
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 2. USER ROLE SIMULATION PICKER ---
st.set_page_config(page_title="Hierarchical BCC Chat", layout="centered")
st.title("🛡️ Hierarchical BCC Chat Prototype")
st.caption("Fabulous Idea Test Environment - Simulating Client, Lead & BCC Observers")

# Sidebar to switch profiles during testing
st.sidebar.header("Testing Control Room")
test_profile = st.sidebar.selectbox(
    "Login as User Profile:",
    ["Client_John (Admin/Client)", "Test_Lead_Amit (Lead)", "Tester_Rahul (BCC Tester)"]
)

# Extract username based on selection (gets 'Client_John', 'Test_Lead_Amit', or 'Tester_Rahul')
current_user = test_profile.split(" ")[0]

# Fetch current user permissions from Supabase
user_data = supabase.table("group_members").select("*").eq("username", current_user).execute()
if user_data.data:
    user_role = user_data.data[0]['role']
    user_can_reply = user_data.data[0]['can_reply']
else:
    st.error(f"User '{current_user}' not found in permissions registry table ('group_members').")
    st.stop()

# --- 3. THE LIVE MEMBER DIRECTORY LAYER ---
st.write("### 👥 Group Members Info View")

# Logic Implementation: Filter the list based on your core rule
if user_role == "Admin_Client":
    # The client ONLY sees non-BCC members. BCC observers are completely hidden!
    members_query = supabase.table("group_members").select("username, role").neq("role", "BCC_Observer").execute()
    st.info("ℹ️ You see exactly 2 members in this group.")
else:
    # Leads and BCC members can see everyone listed
    members_query = supabase.table("group_members").select("username, role").execute()

# Display the scannable member list
for member in members_query.data:
    role_badge = "👑 Creator" if member['role'] == "Admin_Client" else ("⭐ Authorized Lead" if member['role'] == "Lead" else "👻 BCC Observer")
    st.text(f"• {member['username']} ({role_badge})")

st.markdown("---")

# --- 4. THE LIVE CHAT STREAM ENGINE ---
st.write("### 💬 Live Group Chat Feed (`IMP_Discussion`)")

# Fetch all messages from the database
messages_query = supabase.table("chat_messages").select("*").order("created_at", desc=False).execute()

# Display the messages using native stream elements
for msg in messages_query.data:
    # Logic Implementation: Identify who is typing
    if msg['sender'] == current_user:
        with st.chat_message("user"):
            st.markdown(f"**You** : {msg['message_text']}")
    else:
        with st.chat_message("assistant"):  # Changed 'ambient' to 'assistant' as 'ambient' isn't a native Streamlit default icon
            st.markdown(f"**{msg['sender']}**: {msg['message_text']}")

# --- 5. ENFORCING INTERACTION REPLY PERMISSIONS ---
if user_can_reply:
    # If user has explicit permission to reply, render an active chat bar
    if user_input := st.chat_input("Type your message here to the group..."):
        # Save message directly to Supabase
        supabase.table("chat_messages").insert({"sender": current_user, "message_text": user_input}).execute()
        time.sleep(0.5)
        st.rerun()
else:
    # Logic Implementation: Lock out input interface completely for BCC Observers
    st.error("🔒 Your message box is locked. You are viewing this channel as an authorized BCC Observer.")
    st.caption("You have real-time sight of this discussion, but your presence is hidden from the client and you cannot reply.")

# Auto-refresh helper button for testing across screens
if st.button("🔄 Refresh Live Feed"):
    st.rerun()