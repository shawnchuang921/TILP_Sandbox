# views/admin_tool.py (Handles Authentication, User, and Child Management)
import streamlit as st
import pandas as pd
import hashlib
import uuid
import datetime
from views import database as db # CRITICAL: To read/write user and child data

# --- AUTHENTICATION FUNCTIONS ---

def hash_password(password):
    """Hashes a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def show_login_page():
    """Displays the login form."""
    st.title("Login to TILP Connect App")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            users_df = db.get_data('users')
            
            # Check if user exists and password matches
            if users_df.empty:
                st.error("No users found. Please contact the administrator.")
                return

            hashed_input = hash_password(password)
            
            user_data = users_df[users_df['username'] == username]
            
            if not user_data.empty and user_data['password'].iloc[0] == hashed_input:
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.session_state['user_role'] = user_data['role'].iloc[0]
                st.session_state['child_link'] = user_data['child_link'].iloc[0] # For parents
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid Username or Password")

def logout_user():
    """Logs out the current user."""
    keys_to_delete = ['authenticated', 'username', 'user_role', 'menu_selection', 'child_link']
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    st.info("You have been logged out.")
    st.rerun()


# --- CHILD MANAGEMENT FUNCTIONS ---

def show_child_management():
    """Displays forms to add/manage children and related lists."""
    st.subheader("Manage Children, Disciplines, and Goal Areas")

    # 1. Manage Children
    st.markdown("#### 👤 Add New Child")
    with st.form("add_child_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            child_name = st.text_input("Child's Full Name")
        with col2:
            parent_username = st.text_input("Parent's Username (Must Exist)")
        with col3:
            date_of_birth = st.date_input("Date of Birth", datetime.date(2018, 1, 1))

        submitted = st.form_submit_button("Add Child")
        
        if submitted:
            if not child_name or not parent_username:
                st.error("Child Name and Parent Username are required.")
            elif db.get_data('users')[db.get_data('users')['username'] == parent_username].empty:
                st.error(f"User '{parent_username}' does not exist. Please create the parent account first.")
            else:
                new_child = {
                    'child_name': child_name,
                    'parent_username': parent_username,
                    'date_of_birth': date_of_birth
                }
                if db.add_data('children', new_child):
                    st.success(f"Child {child_name} added successfully! Click 'Save Data to GitHub Permanently'.")
                else:
                    st.error("Failed to add child.")

    st.markdown("#### 👶 Existing Children")
    children_df = db.get_data('children')
    if not children_df.empty:
        st.dataframe(children_df)
        
        # Simple Delete functionality
        child_to_delete = st.selectbox("Select Child to Delete (ID)", [''] + children_df['id'].unique().astype(str).tolist(), key="del_child")
        if child_to_delete and st.button("Delete Selected Child", key="del_child_btn"):
            if db.delete_data('children', int(child_to_delete)):
                st.success("Child deleted successfully! Click 'Save Data to GitHub Permanently'.")
                st.rerun()
            else:
                st.error("Failed to delete child.")
    else:
        st.info("No children registered yet.")


    st.markdown("---")
    # 2. Manage Disciplines and Goal Areas
    
    colA, colB = st.columns(2)

    with colA:
        st.markdown("#### 🧩 Manage Disciplines")
        with st.form("add_discipline_form", clear_on_submit=True):
            name = st.text_input("New Discipline Name")
            submitted = st.form_submit_button("Add Discipline")
            if submitted and name:
                db.add_data('disciplines', {'name': name})
                st.success("Discipline added.")
        st.dataframe(db.get_list_data('disciplines'))

    with colB:
        st.markdown("#### 🎯 Manage Goal Areas")
        with st.form("add_goal_area_form", clear_on_submit=True):
            name = st.text_input("New Goal Area Name")
            submitted = st.form_submit_button("Add Goal Area")
            if submitted and name:
                db.add_data('goal_areas', {'name': name})
                st.success("Goal Area added.")
        st.dataframe(db.get_list_data('goal_areas'))


# --- USER MANAGEMENT FUNCTIONS (Placeholder) ---

# Since you don't have a separate user_management.py, we assume this function
# is also located in admin_tool.py.
def show_user_management():
    """Displays forms to add/manage users (Admin role only)."""
    st.subheader("Manage Users (Staff/Parent Accounts)")

    # 1. Add User Form
    st.markdown("#### 🧑‍💻 Add New User Account")
    with st.form("add_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("New Username")
            new_password = st.text_input("Set Password", type="password")
        with col2:
            new_role = st.selectbox("Role", ['staff', 'parent', 'admin'])
            # Only required for parent accounts (parent needs to be linked to a child)
            child_link_id = st.text_input("Child Link (e.g., All or specific child ID for parent)")
        
        submitted = st.form_submit_button("Create User")

        if submitted:
            if db.get_data('users')[db.get_data('users')['username'] == new_username].empty:
                new_user = {
                    'username': new_username,
                    'password': hash_password(new_password),
                    'role': new_role,
                    'child_link': child_link_id if new_role == 'parent' else 'All' 
                }
                if db.add_data('users', new_user):
                    st.success(f"User '{new_username}' created successfully! Click 'Save Data to GitHub Permanently'.")
                else:
                    st.error("Failed to create user.")
            else:
                st.error("Username already exists.")

    st.markdown("#### 📝 Existing Users")
    users_df = db.get_data('users')
    if not users_df.empty:
        # Hide passwords before displaying
        display_df = users_df.drop(columns=['password'], errors='ignore')
        st.dataframe(display_df)
    else:
        st.info("No user accounts found.")
