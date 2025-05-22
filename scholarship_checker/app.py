import streamlit as st
import pandas as pd
from src import parsers
from src.column_utils import extract_column_names, get_standardized_column_name, DEFAULT_MAPPING_RULES
from src.matcher import find_duplicates 
import io 

# Helper function to convert DataFrame to Excel for download
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Results')
    processed_data = output.getvalue()
    return processed_data

def load_client_file(uploaded_file):
    file_name = uploaded_file.name
    file_content = uploaded_file 

    if file_name.endswith(('.xlsx', '.xls')):
        st.info(f"Parsing Excel file: {file_name}")
        parsed_data = parsers.parse_excel(file_content, file_name)
        if not parsed_data:
            st.error(f"Failed to parse Excel file: {file_name}. It might be empty, corrupted, or an unsupported format.")
            return None
        return parsed_data
    elif file_name.endswith('.pdf'):
        st.info(f"Parsing PDF file: {file_name}")
        parsed_data = parsers.parse_pdf(file_content, file_name)
        if not parsed_data: 
            st.warning(f"No tables found or failed to parse PDF file: {file_name}.")
            return [] 
        return parsed_data
    elif file_name.endswith(('.docx', '.doc')):
        st.info(f"Parsing Word file: {file_name}")
        parsed_data = parsers.parse_word(file_content, file_name)
        if not parsed_data: 
            st.error(f"Failed to parse Word file: {file_name}. It might be empty, not a valid Word document, or contain no tables.")
            return None
        return parsed_data
    else:
        st.error(f"Unsupported file type: {file_name}. Please upload .xlsx, .xls, .pdf, .doc, or .docx files.")
        return None

def main():
    st.title("Scholarship Eligibility Checker")

    st.write("Welcome to the Scholarship Eligibility Checker.")
    st.write("Upload files, select columns, and run matching to find duplicates.")

    # Initialize session state variables
    if 'client_data' not in st.session_state: st.session_state.client_data = None
    if 'db_data_collection' not in st.session_state: st.session_state.db_data_collection = {}
    if 'selected_client_columns_original' not in st.session_state: st.session_state.selected_client_columns_original = []
    if 'selected_db_columns_original' not in st.session_state: st.session_state.selected_db_columns_original = []
    if 'results_df' not in st.session_state: st.session_state.results_df = None
    if 'client_file_processed' not in st.session_state: st.session_state.client_file_processed = False
    if 'last_client_file_name' not in st.session_state: st.session_state.last_client_file_name = None
    if 'last_db_files_count' not in st.session_state: st.session_state.last_db_files_count = 0
    if 'db_files_processed_names' not in st.session_state: st.session_state.db_files_processed_names = []


    st.sidebar.header("Upload Files")
    client_file = st.sidebar.file_uploader("Upload Client File (.xlsx, .xls, .pdf, .doc, .docx)", type=['xlsx', 'xls', 'pdf', 'doc', 'docx'], key="client_uploader")
    db_files = st.sidebar.file_uploader("Upload Database Excel Files (.xlsx, .xls)", type=['xlsx', 'xls'], accept_multiple_files=True, key="db_uploader")

    # --- Client File Section ---
    if client_file:
        # Re-process client file if it's new or hasn't been processed yet
        if not st.session_state.client_file_processed or st.session_state.last_client_file_name != client_file.name:
            st.subheader("Client File Processing")
            st.session_state.client_data = load_client_file(client_file)
            st.session_state.selected_client_columns_original = [] 
            st.session_state.results_df = None 
            st.session_state.client_file_processed = True
            st.session_state.last_client_file_name = client_file.name
            
            # Display client file parsing status
            if st.session_state.client_data is not None:
                has_content = False
                if isinstance(st.session_state.client_data, dict) and any(not df.empty for df in st.session_state.client_data.values()):
                    has_content = True
                    file_type_desc = "Excel"
                    num_items_desc = f"{len(st.session_state.client_data)} sheet(s)"
                elif isinstance(st.session_state.client_data, list) and any(isinstance(df, pd.DataFrame) and not df.empty for df in st.session_state.client_data):
                    has_content = True
                    file_type_desc = "PDF" if client_file.name.endswith('.pdf') else "Word"
                    num_items_desc = f"{sum(1 for df in st.session_state.client_data if isinstance(df, pd.DataFrame) and not df.empty)} table(s)"
                
                if has_content:
                    st.success(f"Client file: {client_file.name} ({file_type_desc}, {num_items_desc}) parsed.")
                # If client_data is an empty list (e.g. PDF/Word with no tables) or dict with empty DFs, load_client_file already shows a warning/error.
            
        # Display client data previews and column selection if data is loaded
        if st.session_state.client_data is not None:
            client_data_has_content = False
            if isinstance(st.session_state.client_data, dict) and any(not df.empty for df in st.session_state.client_data.values()):
                client_data_has_content = True
            elif isinstance(st.session_state.client_data, list) and any(isinstance(df, pd.DataFrame) and not df.empty for df in st.session_state.client_data):
                client_data_has_content = True

            if client_data_has_content:
                with st.expander("Show Client Data Preview", expanded=False): # Default to collapsed
                    if isinstance(st.session_state.client_data, dict): # Excel
                        for sheet_name, df in st.session_state.client_data.items():
                            if not df.empty:
                                st.subheader(f"Preview of sheet: {sheet_name}")
                                st.dataframe(df.head())
                            else:
                                st.markdown(f"Sheet: *{sheet_name}* is empty.")
                    elif isinstance(st.session_state.client_data, list): # PDF/Word
                        for idx, df in enumerate(st.session_state.client_data):
                            if isinstance(df, pd.DataFrame) and not df.empty:
                                source_name = df.attrs.get('source', f"Table {idx+1}")
                                st.subheader(f"Preview of table: {source_name}")
                                st.dataframe(df.head())
                            # else: (no need to message for empty individual tables if some have content)

                st.subheader("Select Client File Columns for Matching")
                client_all_columns = extract_column_names(st.session_state.client_data)
                if not client_all_columns:
                    st.warning("No columns found in the client file to select.")
                else:
                    client_column_options = {f"{original_col} (Std: {get_standardized_column_name(original_col, DEFAULT_MAPPING_RULES)})": original_col for original_col in client_all_columns}
                    selected_display = st.multiselect("Select 1 or 2 client columns:", options=list(client_column_options.keys()), max_selections=2, key="client_cols_select_ms", default=[k for k,v in client_column_options.items() if v in st.session_state.selected_client_columns_original])
                    st.session_state.selected_client_columns_original = [client_column_options[disp_name] for disp_name in selected_display]
                    if st.session_state.selected_client_columns_original:
                        st.info(f"Selected client columns: {', '.join(st.session_state.selected_client_columns_original)}")
            # elif isinstance(st.session_state.client_data, list) and not st.session_state.client_data: (already handled by load_client_file warning)
            #    pass


    # --- Database Files Section ---
    if db_files:
        current_db_file_names = sorted([f.name for f in db_files])
        # Re-process DB files if the list of files changes or if no DB data is currently loaded
        if st.session_state.db_files_processed_names != current_db_file_names or not st.session_state.db_data_collection:
            st.subheader("Database Files Processing")
            st.session_state.db_data_collection = {} 
            st.session_state.selected_db_columns_original = [] 
            st.session_state.results_df = None 
            
            processed_db_count = 0
            for db_file_obj in db_files:
                st.write(f"Processing database file: {db_file_obj.name}...")
                parsed_db_sheets = parsers.parse_excel(db_file_obj, db_file_obj.name)
                if parsed_db_sheets and any(not df.empty for df in parsed_db_sheets.values()):
                    st.session_state.db_data_collection[db_file_obj.name] = parsed_db_sheets
                    processed_db_count += 1
                    st.success(f"Parsed: {db_file_obj.name} - found {len(parsed_db_sheets)} sheet(s) with data.")
                elif parsed_db_sheets: # Parsed but all sheets are empty
                     st.warning(f"Parsed: {db_file_obj.name}, but all sheets are empty.")
                # else: parse_excel already logs error

            st.session_state.db_files_processed_names = current_db_file_names
            st.session_state.last_db_files_count = len(db_files) # Though name check is more robust
            
            if st.session_state.db_data_collection:
                 st.info(f"Total {processed_db_count} database file(s) successfully parsed with data.")
            elif db_files: # Files were uploaded, but none yielded data
                st.warning("Uploaded database files were processed, but none contained usable data or tables after parsing.")
            # If no db_files were uploaded, no message is needed here for DB processing

        if st.session_state.db_data_collection:
            with st.expander("Show Database Files Preview", expanded=False): # Default to collapsed
                for db_file_name, sheets_data in st.session_state.db_data_collection.items():
                    st.subheader(f"Preview of database file: {db_file_name}")
                    if not sheets_data:
                        st.markdown("*No sheets found or all sheets are empty in this file.*")
                        continue
                    for sheet_name, df in sheets_data.items():
                        if not df.empty:
                            st.markdown(f"**Sheet: {sheet_name}**")
                            st.dataframe(df.head())
                        else:
                             st.markdown(f"Sheet: *{sheet_name}* is empty.")
            
            st.subheader("Select Database Columns for Matching")
            all_db_dfs = [df for file_data in st.session_state.db_data_collection.values() for df in file_data.values() if isinstance(df, pd.DataFrame) and not df.empty]
            if not all_db_dfs:
                st.warning("No data tables with columns found in the parsed database files for selection.")
            else:
                db_all_columns = extract_column_names(all_db_dfs)
                if not db_all_columns:
                    st.warning("No columns found in the database files to select.")
                else:
                    db_column_options = {f"{original_col} (Std: {get_standardized_column_name(original_col, DEFAULT_MAPPING_RULES)})": original_col for original_col in db_all_columns}
                    selected_db_display = st.multiselect("Select 1 or 2 database columns:", options=list(db_column_options.keys()), max_selections=2, key="db_cols_select_ms", default=[k for k,v in db_column_options.items() if v in st.session_state.selected_db_columns_original])
                    st.session_state.selected_db_columns_original = [db_column_options[disp_name] for disp_name in selected_db_display]
                    if st.session_state.selected_db_columns_original:
                        st.info(f"Selected database columns: {', '.join(st.session_state.selected_db_columns_original)}")

    # --- Matching Section ---
    st.header("Run Matching")
    can_run_matching = (st.session_state.client_data is not None and \
                        st.session_state.db_data_collection and \
                        len(st.session_state.selected_client_columns_original) > 0 and \
                        len(st.session_state.selected_db_columns_original) > 0)

    if not can_run_matching:
        st.warning("Please upload client and database files, ensure they are parsed successfully, and select columns for matching from both.")

    fuzzy_threshold = st.slider("Fuzzy Match Sensitivity (0-100)", min_value=0, max_value=100, value=85, key="fuzzy_slider")

    if st.button("Run Matching", disabled=not can_run_matching):
        with st.spinner("Finding duplicates... This may take a while."):
            st.session_state.results_df = find_duplicates(
                client_data_parsed=st.session_state.client_data,
                selected_client_columns_original=st.session_state.selected_client_columns_original,
                db_data_parsed=st.session_state.db_data_collection,
                selected_db_columns_original=st.session_state.selected_db_columns_original,
                fuzzy_threshold=fuzzy_threshold
            )
        
        if st.session_state.results_df is not None and not st.session_state.results_df.empty:
            st.success("Matching process completed!")
        elif st.session_state.results_df is not None and st.session_state.results_df.empty:
             st.info("Matching process completed. No duplicates found or no client data to process.")
        else: 
            st.error("An unexpected issue occurred during matching.")

    if st.session_state.results_df is not None and not st.session_state.results_df.empty:
        st.subheader("Matching Results")
        st.dataframe(st.session_state.results_df)

        total_client_entries = len(st.session_state.results_df)
        duplicates_found = len(st.session_state.results_df[st.session_state.results_df['status'] == "Duplicate Found"])
        not_found = len(st.session_state.results_df[st.session_state.results_df['status'] == "Not Found"])
        skipped = len(st.session_state.results_df[st.session_state.results_df['status'] == "Skipped (Empty Client Data)"])

        st.subheader("Summary Statistics")
        st.write(f"Total client entries processed: {total_client_entries}")
        st.write(f"Number of 'Duplicate Found': {duplicates_found}")
        st.write(f"Number of 'Not Found': {not_found}")
        if skipped > 0: st.write(f"Number of client entries skipped (empty data): {skipped}")

        excel_data = to_excel(st.session_state.results_df)
        st.download_button(label="Export Results to Excel", data=excel_data, file_name="matching_results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="export_button")
    elif st.session_state.results_df is not None and st.session_state.results_df.empty:
        st.info("No results to display or export from the latest matching run.")

if __name__ == "__main__":
    main()
