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

# Add view_limit for pagination
INITIAL_VIEW_LIMIT = 5
LOAD_INCREMENT = 5
if 'view_limit' not in st.session_state:
    st.session_state.view_limit = INITIAL_VIEW_LIMIT

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"  # Base URL of your FastAPI backend

# --- Helper Functions ---

@st.cache_data(ttl=300) # Cache for 5 minutes
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

# --- Callback Functions (Define before use) ---
def handle_bulk_delete():
    """Callback function to handle bulk deletion."""
    block_ids_to_delete = list(st.session_state.selected_block_ids)
    if not block_ids_to_delete:
        st.warning("No blocks selected for deletion.")
        return

    success, _ = delete_blocks_bulk(block_ids_to_delete)
    if success:
        st.toast(f"Successfully deleted {len(block_ids_to_delete)} block(s).")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.history.insert(0, f"[{timestamp}] Deleted {len(block_ids_to_delete)} blocks: {', '.join(block_ids_to_delete)}")
        st.session_state.history = st.session_state.history[:20]
        # Clear the selected IDs after successful deletion
        st.session_state.selected_block_ids.clear()
        # Clear the cache for the block list
        get_all_blocks.clear()
    # Error message handled by delete_blocks_bulk

# --- Callback for Checkbox Change ---
def update_selection(block_id):
    """Callback to update selected_block_ids based on checkbox state."""
    checkbox_key = f"select_{block_id}"
    if st.session_state[checkbox_key]: # If checkbox is checked
        st.session_state.selected_block_ids.add(block_id)
    elif block_id in st.session_state.selected_block_ids: # If checkbox is unchecked AND was in the set
        st.session_state.selected_block_ids.remove(block_id)

# --- Streamlit App Layout ---
st.set_page_config(page_title="StateLock Memory Assistant", layout="wide")

st.title(" StateLock Engine - Memory Block Assistant")
st.caption("Interact with the Memory Block API.")

# Define columns for layout
col1, col2 = st.columns(2)

# --- COLUMN 1 --- #
with col1:
    # Display delete button and count only if items are selected (Moved higher for visibility)
    selected_count = len(st.session_state.selected_block_ids)
    if selected_count > 0:
        st.write(f"{selected_count} block(s) selected for deletion.")
        st.button(f"Delete Selected ({selected_count}) Blocks", 
                  key="bulk_delete_button", 
                  on_click=handle_bulk_delete)
        st.divider() # Add divider only when delete button is shown

    # --- View All Blocks Section ---
    st.subheader("View All Memory Blocks")
    # Display the info text here only if NO blocks are selected
    if selected_count == 0:
        st.caption("Select blocks using checkboxes below to perform bulk operations.")

    # Fetch blocks using the cached function
    blocks = get_all_blocks()

    if blocks:
        # Display based on view_limit
        st.write(f"Displaying {min(len(blocks), st.session_state.view_limit)} of {len(blocks)} blocks:")
        # Iterate only over the blocks within the current limit
        for block in blocks[:st.session_state.view_limit]:
            block_id = block.get('id')
            if block_id:
                # Checkbox for selection (ensure unique key using block_id)
                # Use on_change callback to update state immediately
                st.checkbox(f"Select##{block_id}", 
                                          value=(block_id in st.session_state.selected_block_ids), 
                                          key=f"select_{block_id}",
                                          on_change=update_selection,
                                          args=(block_id,))
                
                # Display block details in expander
                with st.expander(f"**{block.get('name', 'Unnamed Block')}** (ID: ...{block_id[-8:]})"):
                    st.write("**ID:**")
                    st.code(block_id, language=None) 
                    st.write("**Content:**")
                    st.text(block.get('content', '(Content not available)'))
        
        # Show 'Load More' button if there are more blocks than the current limit
        if len(blocks) > st.session_state.view_limit:
            if st.button(f"Load {LOAD_INCREMENT} More"):
                st.session_state.view_limit += LOAD_INCREMENT
                st.rerun() # Rerun to display the newly loaded blocks
        # Option to reset view limit
        if st.session_state.view_limit > INITIAL_VIEW_LIMIT:
             if st.button("Show Fewer"):
                 st.session_state.view_limit = INITIAL_VIEW_LIMIT
                 st.rerun()
                 
    else:
        st.info("No memory blocks found in the database.")

    st.divider() # Divider after View All in col1

# --- COLUMN 2 --- #
with col2:
    st.subheader("History/Recent Activity")
    st.write("Recent Activity (Last 5):")
    if not st.session_state.history:
        st.caption("No activity recorded yet.")
    else:
        for history_item in st.session_state.history[:5]:
            st.caption(history_item) # Use caption for less emphasis
    st.divider() # Add divider after history

    # --- Add New Block Section (Now in col2) ---
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
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.history.insert(0, f"[{timestamp}] Added block: {new_block_data.get('name', 'Unnamed')} (ID: ...{new_block_data.get('id', '')[-8:]})")
                    st.session_state.history = st.session_state.history[:20]
                    get_all_blocks.clear()
                    st.session_state.view_limit = INITIAL_VIEW_LIMIT # Reset view limit after adding
                    st.rerun()

    st.divider()

    # --- Query Memory Blocks Section (Now in col2) ---
    st.subheader("Query Memory Blocks")

    query_text = st.text_area("Query Text", key="query_text_input")
    top_k = st.number_input("Number of results (top_k)", min_value=1, max_value=10, value=3, key="top_k_input")

    if st.button("Run Query", key="query_button"):
        if not query_text:
            st.warning("Please enter query text.")
        else:
            success, results = query_blocks(query_text, top_k)
            if success:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Timestamp for history
                if results:
                    st.success(f"Found {len(results)} relevant block(s):")
                    st.session_state.history.insert(0, f"[{timestamp}] Ran query: '{query_text[:50]}{'...' if len(query_text) > 50 else ''}' (Found {len(results)})")
                    # Display query results directly in col2 below the query input
                    for i, result in enumerate(results):
                        with st.expander(f"**Result {i+1}: {result.get('name', 'Unnamed Block')}** (Distance: {result.get('distance', 'N/A'):.4f})"):
                            st.write("**ID:**")
                            st.code(result.get('id', 'N/A'), language=None)
                            st.write("**Content:**")
                            st.text(result.get('content', '(Content not available)'))
                else:
                    st.info("No relevant blocks found for this query.")
                    st.session_state.history.insert(0, f"[{timestamp}] Ran query: '{query_text[:50]}{'...' if len(query_text) > 50 else ''}' (Found 0)")
                st.session_state.history = st.session_state.history[:20] # Limit history
