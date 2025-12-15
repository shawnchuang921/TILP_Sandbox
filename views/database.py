# views/database.py (UPDATED for GitHub CSV Persistence)
import pandas as pd
import os
import streamlit as st # Need Streamlit for st.secrets and file handling

DATA_DIR = "data"

def init_db():
    """Ensure the data directory exists (local development only)."""
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
        # This should not happen if the initial files were committed
        st.error(f"FATAL: Database file not found: {csv_path}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data for {table_name}: {e}")
        return pd.DataFrame()

def _save_data(df, table_name):
    """Saves a DataFrame back to its CSV file."""
    csv_path = _get_csv_path(table_name)
    # Use index=False to prevent saving the DataFrame row index
    df.to_csv(csv_path, index=False)
    # In the deployed environment, this only saves it temporarily to the server's disk. 
    # The 'Save to GitHub' function (in app.py) will make it permanent.


# --- PUBLIC FUNCTIONS (The API used by the app) ---

# NOTE: The public functions (get_data, add_data, delete_data, update_data) remain 
# the same as the final CSV migration code I provided previously. 
# They simply call the updated _load_data and _save_data helpers.

def get_data(table_name):
    """Retrieves all data from a specified table (CSV file)."""
    return _load_data(table_name)

def get_list_data(table_name):
    """A wrapper for get_data, currently only used for disciplines and goal_areas."""
    return _load_data(table_name)

def add_data(table_name, new_data):
    """Adds a new row of data to the specified table."""
    df = _load_data(table_name)

    # 1. Determine new ID
    if table_name != 'users': 
        next_id = df['id'].max() + 1 if not df.empty and 'id' in df.columns and pd.notna(df['id'].max()) else 1
        new_data['id'] = next_id

    # 2. Convert new data to DataFrame row
    # Ensure new_data keys match df columns if df is not empty
    new_row = pd.DataFrame([new_data], columns=df.columns)

    # 3. Concatenate and Save
    updated_df = pd.concat([df, new_row], ignore_index=True)
    _save_data(updated_df, table_name)

    return True # Success

def delete_data(table_name, row_id):
    """Deletes a row by its 'id'."""
    df = _load_data(table_name)

    # Filter out the row to be deleted
    updated_df = df[df['id'] != row_id].copy()

    # Save the updated DataFrame
    _save_data(updated_df, table_name)

    return True # Success

def update_data(table_name, row_id, updated_data):
    """Updates an existing row by its 'id'."""
    df = _load_data(table_name)

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

# Initialize the data directory (only runs in local environment)
init_db()
