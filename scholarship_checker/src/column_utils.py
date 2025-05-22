import pandas as pd
import re

DEFAULT_MAPPING_RULES = {
    "name": ["name", "student name", "applicant name", "name / father's name", "name of student", "candidate name", "student_name", "applicant_name"],
    "roll_number": ["roll no", "roll number", "application no", "application id", "registration no", "roll_no", "roll_number", "application_no", "application_id", "registration_no", "student id", "admission no", "scholar no", "student_id", "admission_no", "scholar_no"],
    "mobile_number": ["mobile", "mobile no", "mobile number", "phone", "phone no", "phone number", "contact no", "contact number", "mobile_no", "mobile_number", "phone_no", "phone_number"],
    "email": ["email", "email id", "email address", "email_id", "email_address"],
    "father_name": ["father name", "father's name", "fathers name", "father_name"],
    "dob": ["dob", "date of birth", "birth date", "date_of_birth"],
    # Add more common mappings as needed
}

def extract_column_names(data_object):
    """
    Extracts all unique, sorted column names from a data object.
    Data object can be a list of DataFrames or a dictionary of {sheet_name: DataFrame}.
    """
    all_columns = set()
    if isinstance(data_object, list): # List of DataFrames (e.g., from PDF/Word)
        for df in data_object:
            if isinstance(df, pd.DataFrame):
                all_columns.update(df.columns.tolist())
    elif isinstance(data_object, dict): # Dict of DataFrames (e.g., from Excel)
        for df in data_object.values():
            if isinstance(df, pd.DataFrame):
                all_columns.update(df.columns.tolist())
    elif isinstance(data_object, pd.DataFrame): # Single DataFrame
        all_columns.update(data_object.columns.tolist())
        
    return sorted(list(all_columns))

def get_standardized_column_name(column_name, mapping_rules=DEFAULT_MAPPING_RULES):
    """
    Standardizes a column name based on mapping rules.
    """
    if not isinstance(column_name, str): # Handle non-string inputs gracefully
        return str(column_name) # Or raise an error, or return as is

    cleaned_name = str(column_name).lower().strip()
    cleaned_name = re.sub(r'[\s_-]+', ' ', cleaned_name) # Replace common separators with space and collapse multiple spaces

    for standard_name, variations in mapping_rules.items():
        if cleaned_name in variations:
            return standard_name
    return column_name # Return original if no mapping found (or its cleaned version, depending on preference)

def generate_standardized_column_map(data_frames):
    """
    Generates a map from original column names to their standardized versions
    for all columns in the provided data_frames (list or dict of DataFrames).
    """
    original_to_standardized_map = {}
    all_original_columns = extract_column_names(data_frames)
    
    for original_col in all_original_columns:
        original_to_standardized_map[original_col] = get_standardized_column_name(original_col)
        
    return original_to_standardized_map

def clean_column_values(series):
    """
    Cleans string values in a pandas Series: converts to lowercase, strips whitespace,
    and replaces multiple spaces with a single space.
    """
    if not isinstance(series, pd.Series):
        # Consider logging this or raising an error if the input is not a Series
        return series 

    # Check if the series dtype suggests it contains string-like data
    # Check for object dtype or string dtype explicitly
    if series.dtype == 'object' or pd.api.types.is_string_dtype(series):
        # Convert to string to handle potential mixed types (e.g., numbers read as objects)
        cleaned_series = series.astype(str).str.lower().str.strip()
        cleaned_series = cleaned_series.str.replace(r'\s+', ' ', regex=True)
        return cleaned_series
    return series # Return original series if not object/string type

# Example Usage (can be removed or kept for testing)
if __name__ == '__main__':
    # Test extract_column_names
    df1 = pd.DataFrame({'Applicant Name': ['Alice'], 'Roll No': [1]})
    df2 = pd.DataFrame({'Name': ['Bob'], 'Application ID': [2], 'Mobile': [123]})
    print(f"Extracted from list: {extract_column_names([df1, df2])}")
    print(f"Extracted from dict: {extract_column_names({'Sheet1': df1, 'Sheet2': df2})}")

    # Test get_standardized_column_name
    print(f"Standard for 'Student Name': {get_standardized_column_name('Student Name')}")
    print(f"Standard for 'ROLL_NUMBER': {get_standardized_column_name('ROLL_NUMBER')}")
    print(f"Standard for 'Unmapped Column': {get_standardized_column_name('Unmapped Column')}")

    # Test generate_standardized_column_map
    print(f"Standard map for list: {generate_standardized_column_map([df1, df2])}")
    
    # Test clean_column_values
    s = pd.Series(["  Test Value 1 ", "TEST VALUE 2  ", " Test   Value 3", 123, None])
    print(f"Cleaned series:\n{clean_column_values(s)}")
    
    num_s = pd.Series([1, 2, 3])
    print(f"Cleaned numeric series:\n{clean_column_values(num_s)}")
