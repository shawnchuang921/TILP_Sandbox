# views/database.py (UPDATED for GitHub CSV Persistence)
import pandas as pd
import os
import streamlit as st # CRITICAL: Needed for st.secrets and st.error

DATA_DIR = "data"

def init_db():
    """Ensure the data directory exists (local development only)."""
    # In Streamlit Cloud, the 'data' directory is already created by Git checkout
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

# --- HELPER FUNCTIONS ---

def _get_csv_path(table_name):
    """Returns the absolute path to a CSV file for a given table name."""
    return os.path.join(DATA_DIR, f"{table_name}.csv")

def _load_data(table_name):
    """Loads a DataFrame from a CSV file."""
    csv_path = _get_csv_path(table_name)
    try:
        df = pd.read_csv(csv_path)
        # Handle the special case where 'date' columns might need to be parsed
        if table_name in ['progress', 'session_plans', 'children']:
            for col in ['date', 'date_of_birth']:
                if col in df.columns:
                    # Coerce invalid dates to NaT (Not a Time)
                    df[col] = pd.to_datetime(df[col], errors='coerce')
        return df
    except FileNotFoundError:
        # This will happen if the initial empty CSV files were not committed to 'data'
        st.error(f"FATAL: Database file not found: {csv_path}. Please check your 'data' folder.")
        return pd.DataFrame()
    except Exception as e:
        # Catches errors like empty files without headers
        st.error(f"Error loading data for {table_name}: {e}. Check file headers.")
        return pd.DataFrame()

def _save_data(df, table_name):
    """Saves a DataFrame back to its CSV file (temporarily on the server)."""
    csv_path = _get_csv_path(table_name)
    # Use index=False to prevent saving the DataFrame row index
    df.to_csv(csv_path, index=False)
    # NOTE: The 'Save to GitHub' function in app.py makes this permanent.


# --- PUBLIC FUNCTIONS (The API used by the app) ---
# NOTE: The logic here remains the same as our previous successful CSV migration code.

def get_data(table_name):
    """Retrieves all data from a specified table (CSV file)."""
    return _load_data(table_name)

def get_list_data(table_name):
    """A wrapper for get_data, currently only used for disciplines and goal_areas."""
    # Ensure the dataframe is loaded before checking for 'name'
    df = _load_data(table_name)
    if 'name' in df.columns:
        return df
    return pd.DataFrame()

def add_data(table_name, new_data):
    """Adds a new row of data to the specified table."""
    df = _load_data(table_name)
    
    # 1. Determine new ID
    if table_name not in ['users', 'disciplines', 'goal_areas']: 
        # Only assign ID if the column exists and the table isn't one of the list tables
        if 'id' in df.columns:
            next_id = df['id'].max() + 1 if not df.empty and pd.notna(df['id'].max()) else 1
            new_data['id'] = next_id
    
    # 2. Convert new data to DataFrame row
    # Ensure new_data keys match df columns if df is not empty
    # Handle the case where the DF is empty (first insert)
    columns = df.columns.tolist() if not df.empty else list(new_data.keys())
    new_row = pd.DataFrame([new_data], columns=columns)
    
    # 3. Concatenate and Save
    updated_df = pd.concat([df, new_row], ignore_index=True)
    _save_data(updated_df, table_name)
    
    return True # Success

def delete_data(table_name, row_id):
    """Deletes a row by its 'id'."""
    df = _load_data(table_name)
    
    if 'id' not in df.columns:
        return False # Cannot delete if no ID column exists

    # Filter out the row to be deleted
    updated_df = df[df['id'] != row_id].copy()
    
    # Save the updated DataFrame
    _save_data(updated_df, table_name)
    
    return True # Success

def update_data(table_name, row_id, updated_data):
    """Updates an existing row by its 'id'."""
    df = _load_data(table_name)
    
    if 'id' not in df.columns:
        return False # Cannot update if no ID column exists

    # Find the index of the row to update
    index_to_update = df[df['id'] == row_id].index
    
    if not index_to_update.empty:
        # Update the row with the new values
        for key, value in updated_data.items():
            df.loc[index_to_update, key] = value
            
        # Save the updated DataFrame
        _save_data(df, table_name)
        return True # Success
        
    return False # Row not found

def show_data_analytics():
    """Placeholder function for the Data & Analytics page."""
    # This assumes the function name is show_data_analytics()
    st.markdown("### Raw Data View")
    
    # Simple example to display the tables. You can replace this with your actual analytics logic.
    table_options = ["progress", "session_plans", "children", "users", "disciplines", "goal_areas", "progress_media"]
    selected_table = st.selectbox("Select Table to View", table_options)
    
    df = get_data(selected_table)
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("Table is empty or failed to load.")

# Initialize the data directory (only runs in local environment)
init_db()
