"""
Streamlit Client UI for the Memory Block Assistant API.
"""

import streamlit as st
import requests
import datetime # Import datetime for timestamps

# Initialize session state for history if it doesn't exist
if 'history' not in st.session_state:
    st.session_state.history = []

# Initialize session state for selected IDs if it doesn't exist
if 'selected_block_ids' not in st.session_state:
    st.session_state.selected_block_ids = set()

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"  # Base URL of your FastAPI backend

# --- Helper Functions ---

@st.cache_data
def get_all_blocks():
    """Fetches all blocks from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/memory_blocks/")
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching blocks: {e}")
        return []

def add_block(name: str | None, content: str):
    """Sends a request to add a new block via the API."""
    payload = {"name": name if name else None, "content": content}
    try:
        response = requests.post(f"{API_BASE_URL}/memory_blocks/", json=payload)
        response.raise_for_status()
        return True, response.json() # Return success status and response data
    except requests.exceptions.RequestException as e:
        st.error(f"Error adding block: {e} - {response.text if 'response' in locals() else ''}")
        return False, None # Return failure status

def query_blocks(query_text: str, top_k: int):
    """Sends a query request to the API."""
    payload = {"query_text": query_text, "top_k": top_k}
    try:
        response = requests.post(f"{API_BASE_URL}/memory_blocks/query/", json=payload)
        response.raise_for_status()
        return True, response.json().get('results', []) # Return success status and results list
    except requests.exceptions.RequestException as e:
        st.error(f"Error querying blocks: {e} - {response.text if 'response' in locals() else ''}")
        return False, [] # Return failure status

def delete_blocks_bulk(ids_to_delete: list[str]):
    """Sends a bulk delete request to the API."""
    payload = {"ids": ids_to_delete}
    try:
        response = requests.delete(f"{API_BASE_URL}/memory_blocks/bulk", json=payload)
        response.raise_for_status()
        return True, response.json() # Return success status and response data
    except requests.exceptions.RequestException as e:
        st.error(f"Error during bulk delete: {e} - {response.text if 'response' in locals() else ''}")
        return False, None # Return failure status

# --- Streamlit App Layout ---
st.set_page_config(page_title="StateLock Memory Assistant", layout="wide")

st.title(" StateLock Engine - Memory Block Assistant")
st.caption("Interact with the Memory Block API.")

# --- Sidebar Navigation (Example for future) ---
# st.sidebar.title("Navigation")
# page = st.sidebar.radio("Go to", ["View Blocks", "Add Block", "Query Blocks"])

# --- Main Content Area ---

st.header("View All Memory Blocks")

if st.button("Refresh Block List"):
    st.rerun()

blocks = get_all_blocks() # This now gets content too

if blocks:
    st.write(f"Found {len(blocks)} blocks:")
    for block in blocks:
        block_id = block.get('id')
        if block_id:
            # Checkbox for selection
            is_selected = st.checkbox(f"Select##{block_id}", 
                                      value=(block_id in st.session_state.selected_block_ids), 
                                      key=f"select_{block_id}")
            
            # Update session state based on checkbox
            if is_selected:
                st.session_state.selected_block_ids.add(block_id)
            elif block_id in st.session_state.selected_block_ids:
                st.session_state.selected_block_ids.remove(block_id)

            # Display block details in expander
            with st.expander(f"**{block.get('name', 'Unnamed Block')}**"):
                st.write("**ID:**")
                st.code(block_id, language=None) 
                st.write("**Content:**")
                st.text(block.get('content', '(Content not available)'))
else:
    st.info("No memory blocks found in the database.")

# --- TODO Sections (Based on user requirements) ---
st.divider()
st.subheader("Add New Memory Block")

with st.form(key='add_block_form', clear_on_submit=True):
    new_block_name = st.text_input("Block Name (Optional)")
    new_block_content = st.text_area("Block Content", height=150)
    submit_button = st.form_submit_button(label='Add Block')

    if submit_button:
        if not new_block_content:
            st.warning("Block Content cannot be empty.")
        else:
            success, new_block_data = add_block(new_block_name, new_block_content)
            if success:
                st.success(f"Block '{new_block_data.get('name', new_block_data.get('id'))}' added successfully!")
                # Add to history
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.history.insert(0, f"[{timestamp}] Added block: {new_block_data.get('name', 'Unnamed')} (ID: {new_block_data.get('id')[:8]}...)")
                st.session_state.history = st.session_state.history[:20]
                # Clear the cache for the block list so it refreshes
                get_all_blocks.clear()
                # Rerun to clear form and refresh list
                st.rerun()
            # Error message is handled by the add_block function using st.error

st.divider()
st.subheader("Query Memory Blocks")

query_text = st.text_area("Query Text", key="query_text_input")
top_k = st.number_input("Number of results (top_k)", min_value=1, max_value=10, value=3, key="top_k_input")

if st.button("Run Query", key="query_button"):
    if not query_text:
        st.warning("Please enter query text.")
    else:
        success, results = query_blocks(query_text, top_k)
        if success:
            if results:
                st.success(f"Found {len(results)} relevant block(s):")
                # Add to history
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.history.insert(0, f"[{timestamp}] Ran query: '{query_text[:50]}{'...' if len(query_text) > 50 else ''}' (Found {len(results)} results)")
                # Limit history size (optional)
                st.session_state.history = st.session_state.history[:20] 
                
                for i, result in enumerate(results):
                    with st.expander(f"**Result {i+1}: {result.get('name', 'Unnamed Block')}** (Distance: {result.get('distance', 'N/A'):.4f})"):
                        st.write("**ID:**")
                        st.code(result.get('id', 'N/A'), language=None)
                        st.write("**Content:**")
                        st.text(result.get('content', '(Content not available)'))
            else:
                st.info("No relevant blocks found for this query.")
                # Add to history (even if no results)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.history.insert(0, f"[{timestamp}] Ran query: '{query_text[:50]}{'...' if len(query_text) > 50 else ''}' (Found 0 results)")
                # Limit history size (optional)
                st.session_state.history = st.session_state.history[:20] 
        # Error message is handled by the query_blocks function using st.error

st.divider()
st.subheader("History/Recent Activity")
# Store and display recent actions?
st.write("Recent Activity:")
for history_item in st.session_state.history:
    st.write(history_item)

def handle_bulk_delete():
    """Callback function to handle bulk deletion."""
    ids_to_delete = list(st.session_state.selected_block_ids)
    if not ids_to_delete:
        return
        
    success, result = delete_blocks_bulk(ids_to_delete)
    
    if success:
        deleted_count = result.get('deleted_count', 0)
        # Add to history
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.history.insert(0, f"[{timestamp}] Bulk deleted {deleted_count} blocks.")
        st.session_state.history = st.session_state.history[:20] 
        # Clear selection 
        st.session_state.selected_block_ids.clear()
        # Show a temporary toast message
        st.toast(f"Bulk delete successful. Processed {deleted_count} ID(s).") 
        # Force a rerun to refresh the UI completely after successful deletion
        st.rerun() 
    # Error message handled by delete_blocks_bulk

st.divider()
st.subheader("Bulk Operations")

selected_count = len(st.session_state.selected_block_ids)
if selected_count > 0:
    st.write(f"{selected_count} block(s) selected for deletion.")
    # Use on_click to trigger the callback before the main script rerun
    st.button(f"Delete Selected ({selected_count}) Blocks", 
              key="bulk_delete_button", 
              on_click=handle_bulk_delete)
else:
    st.info("Select blocks using the checkboxes above to perform bulk operations.")
