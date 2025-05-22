import pandas as pd
from rapidfuzz import fuzz, process
from src.column_utils import clean_column_values, get_standardized_column_name, DEFAULT_MAPPING_RULES
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_duplicates(client_data_parsed, selected_client_columns_original, 
                    db_data_parsed, selected_db_columns_original, 
                    fuzzy_threshold=85):
    """
    Finds duplicates between client data and database data using selected columns.
    """
    results_list = []
    
    if not selected_client_columns_original or not selected_db_columns_original:
        logging.warning("Client or DB columns not selected. Aborting matching.")
        return pd.DataFrame()

    std_selected_client_cols = [get_standardized_column_name(col, DEFAULT_MAPPING_RULES) for col in selected_client_columns_original]
    logging.info(f"Standardized selected client columns: {std_selected_client_cols}")

    client_dfs_to_process = []
    if isinstance(client_data_parsed, list): # PDF/Word
        client_dfs_to_process = [df for df in client_data_parsed if isinstance(df, pd.DataFrame) and not df.empty]
    elif isinstance(client_data_parsed, dict): # Excel
        client_dfs_to_process = [df for df in client_data_parsed.values() if isinstance(df, pd.DataFrame) and not df.empty]

    for client_df_idx, client_df in enumerate(client_dfs_to_process):
        # Ensure selected client columns exist in the current client_df
        missing_client_cols = [col for col in selected_client_columns_original if col not in client_df.columns]
        if missing_client_cols:
            logging.warning(f"Client DataFrame (index/sheet {client_df_idx}) is missing selected columns: {', '.join(missing_client_cols)}. Skipping this DataFrame.")
            continue

        # Create combined client match series
        try:
            if len(selected_client_columns_original) == 1:
                client_match_series = clean_column_values(client_df[selected_client_columns_original[0]].astype(str))
            else: # len == 2
                col1_cleaned = clean_column_values(client_df[selected_client_columns_original[0]].astype(str))
                col2_cleaned = clean_column_values(client_df[selected_client_columns_original[1]].astype(str))
                client_match_series = col1_cleaned + " " + col2_cleaned
        except KeyError as e:
            logging.error(f"KeyError while creating client_match_series for client_df {client_df_idx}: {e}. Skipping this DataFrame.")
            continue
            
        logging.info(f"Processing Client DataFrame #{client_df_idx+1} with {len(client_df)} rows.")

        for client_row_index, client_row_data in client_df.iterrows():
            client_match_string = client_match_series.loc[client_row_index]
            if pd.isna(client_match_string) or not client_match_string.strip():
                logging.debug(f"Skipping client row {client_row_index} due to empty match string.")
                # Append a result indicating skipped or not processed, or just skip
                result_entry = client_row_data.to_dict()
                result_entry['status'] = "Skipped (Empty Client Data)"
                result_entry['matched_file'] = None
                result_entry['matched_sheet'] = None
                results_list.append(result_entry)
                continue

            found_flag = False
            matched_file = None
            matched_sheet = None
            # matched_db_row_details = None # Optional

            for db_file_name, sheets_dict in db_data_parsed.items():
                if found_flag: break # Already found for this client row in a previous DB file
                for db_sheet_name, db_df in sheets_dict.items():
                    if found_flag: break # Already found for this client row in a previous sheet

                    # Identify corresponding columns in db_df
                    actual_db_match_cols = []
                    temp_std_db_cols_found = [] # Store standardized names of db columns found

                    # Try to map using standardized names first
                    for std_client_col_target in std_selected_client_cols:
                        found_std_match_for_client_col = False
                        for db_col_original in db_df.columns:
                            std_db_col = get_standardized_column_name(db_col_original, DEFAULT_MAPPING_RULES)
                            if std_db_col == std_client_col_target:
                                actual_db_match_cols.append(db_col_original)
                                temp_std_db_cols_found.append(std_db_col)
                                found_std_match_for_client_col = True
                                break 
                        if not found_std_match_for_client_col:
                            # If a standardized match wasn't found for this specific std_client_col_target,
                            # this db_df might not be suitable based on standardized mapping.
                            # However, we also need to consider the user's explicit DB column selections.
                            pass
                    
                    # If the number of found standardized columns doesn't match, try using selected_db_columns_original
                    # This logic prioritizes standardized mapping but falls back to direct user selection for DB columns.
                    if len(actual_db_match_cols) != len(std_selected_client_cols):
                        actual_db_match_cols = [] # Reset
                        temp_std_db_cols_found = []
                        for s_db_col in selected_db_columns_original:
                            if s_db_col in db_df.columns:
                                actual_db_match_cols.append(s_db_col)
                                temp_std_db_cols_found.append(get_standardized_column_name(s_db_col, DEFAULT_MAPPING_RULES))
                    
                    # Ensure we have the same number of columns for matching as selected for the client
                    if len(actual_db_match_cols) != len(selected_client_columns_original):
                        logging.debug(f"Could not find suitable matching columns in DB sheet: {db_file_name} -> {db_sheet_name} based on client's {len(selected_client_columns_original)} selected columns. Found: {actual_db_match_cols}")
                        continue # Move to the next DB sheet or file
                    
                    logging.debug(f"Using DB columns {actual_db_match_cols} for matching in sheet {db_file_name} -> {db_sheet_name}")

                    # Create combined DB match series
                    try:
                        if len(actual_db_match_cols) == 1:
                            db_match_series = clean_column_values(db_df[actual_db_match_cols[0]].astype(str))
                        else: # len == 2
                            db_col1_cleaned = clean_column_values(db_df[actual_db_match_cols[0]].astype(str))
                            db_col2_cleaned = clean_column_values(db_df[actual_db_match_cols[1]].astype(str))
                            db_match_series = db_col1_cleaned + " " + db_col2_cleaned
                    except KeyError as e:
                        logging.error(f"KeyError creating db_match_series for {db_file_name}/{db_sheet_name}: {e}. Skipping this sheet.")
                        continue
                    
                    # Perform matching
                    db_match_list = db_match_series.tolist()
                    
                    # Exact Match
                    if client_match_string in db_match_list:
                        match_index = db_match_list.index(client_match_string)
                        # matched_db_row_details = db_df.iloc[match_index].to_dict() # Optional
                        found_flag = True
                    
                    # Fuzzy Match (if no exact match)
                    if not found_flag:
                        fuzzy_match_result = process.extractOne(client_match_string, db_match_list, 
                                                                scorer=fuzz.WRatio, score_cutoff=fuzzy_threshold)
                        if fuzzy_match_result:
                            # matched_db_row_details = db_df.iloc[fuzzy_match_result[2]].to_dict() # Optional (fuzzy_match_result[2] is the index)
                            found_flag = True
                    
                    if found_flag:
                        matched_file = db_file_name
                        matched_sheet = db_sheet_name
                        logging.info(f"Match found for client row {client_row_index} in {db_file_name}/{db_sheet_name}.")
                        break # Break from sheets loop

                if found_flag:
                    break # Break from files loop

            result_entry = client_row_data.to_dict()
            result_entry['status'] = "Duplicate Found" if found_flag else "Not Found"
            result_entry['matched_file'] = matched_file
            result_entry['matched_sheet'] = matched_sheet
            # result_entry['matched_db_row'] = matched_db_row_details # Optional
            results_list.append(result_entry)

    if not results_list:
        logging.warning("No results generated. This might be due to no client data or other issues.")
        return pd.DataFrame() # Return empty DataFrame if nothing was processed

    results_df = pd.DataFrame(results_list)
    return results_df
