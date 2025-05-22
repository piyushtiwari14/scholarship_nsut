import pandas as pd
from pandas.testing import assert_series_equal
from scholarship_checker.src.column_utils import clean_column_values, get_standardized_column_name, DEFAULT_MAPPING_RULES, extract_column_names

# Tests for clean_column_values
def test_clean_column_simple():
    input_series = pd.Series(["  Test String  ", "Another One", "  leading space", "trailing space  "])
    expected_series = pd.Series(["test string", "another one", "leading space", "trailing space"])
    cleaned_series = clean_column_values(input_series)
    assert_series_equal(cleaned_series, expected_series, check_dtype=False)

def test_clean_column_with_numbers_and_none():
    input_series = pd.Series(["  Value 1  ", 123, None, "  MIXED Case  "])
    # astype(str) converts None to 'none' and numbers to their string representation
    expected_series = pd.Series(["value 1", "123", "none", "mixed case"])
    cleaned_series = clean_column_values(input_series)
    assert_series_equal(cleaned_series, expected_series, check_dtype=False)

def test_clean_column_all_whitespace_and_empty():
    input_series = pd.Series(["   ", "", "  \t \n "])
    expected_series = pd.Series(["", "", ""]) # Stripped and multiple spaces collapsed
    cleaned_series = clean_column_values(input_series)
    assert_series_equal(cleaned_series, expected_series, check_dtype=False)

def test_clean_column_already_clean():
    input_series = pd.Series(["clean", "already", "perfectly fine"])
    expected_series = pd.Series(["clean", "already", "perfectly fine"])
    cleaned_series = clean_column_values(input_series)
    assert_series_equal(cleaned_series, expected_series, check_dtype=False)

def test_clean_column_non_string_series():
    input_series = pd.Series([1, 2, 3, 4.5])
    expected_series = pd.Series([1, 2, 3, 4.5]) # Should be returned as is
    cleaned_series = clean_column_values(input_series)
    assert_series_equal(cleaned_series, expected_series)


# Tests for get_standardized_column_name
def test_get_standardized_name_exact_match():
    assert get_standardized_column_name("Applicant Name", DEFAULT_MAPPING_RULES) == "name"
    assert get_standardized_column_name("roll no", DEFAULT_MAPPING_RULES) == "roll_number"
    assert get_standardized_column_name("MOBILE", DEFAULT_MAPPING_RULES) == "mobile_number" # Test case insensitivity
    assert get_standardized_column_name("Father's Name", DEFAULT_MAPPING_RULES) == "father_name" # Test with apostrophe

def test_get_standardized_name_variant_match():
    assert get_standardized_column_name("Student_Name", DEFAULT_MAPPING_RULES) == "name" # underscore
    assert get_standardized_column_name("application id", DEFAULT_MAPPING_RULES) == "roll_number" # space
    assert get_standardized_column_name("email address", DEFAULT_MAPPING_RULES) == "email"
    assert get_standardized_column_name("  Date Of Birth  ", DEFAULT_MAPPING_RULES) == "dob" # leading/trailing spaces

def test_get_standardized_name_no_match():
    assert get_standardized_column_name("Unique Header", DEFAULT_MAPPING_RULES) == "unique header" # only cleaned
    assert get_standardized_column_name("Another Special Column", DEFAULT_MAPPING_RULES) == "another special column"

def test_get_standardized_name_with_non_string_input():
    assert get_standardized_column_name(123, DEFAULT_MAPPING_RULES) == "123"
    assert get_standardized_column_name(None, DEFAULT_MAPPING_RULES) == "None"


# Tests for extract_column_names
def test_extract_column_names_list_of_dataframes():
    df1 = pd.DataFrame({'A': [1], 'B': [2]})
    df2 = pd.DataFrame({'C': [3], 'D': [4], 'A': [5]}) # Overlapping column 'A'
    data_object = [df1, df2]
    expected_columns = ['A', 'B', 'C', 'D']
    assert extract_column_names(data_object) == expected_columns

def test_extract_column_names_dict_of_dataframes():
    df1 = pd.DataFrame({'Name': ['Alice'], 'Age': [30]})
    df2 = pd.DataFrame({'City': ['New York'], 'Country': ['USA'], 'Name': ['Bob']})
    data_object = {'Sheet1': df1, 'Sheet2': df2}
    expected_columns = ['Age', 'City', 'Country', 'Name']
    assert extract_column_names(data_object) == expected_columns

def test_extract_column_names_single_dataframe():
    df = pd.DataFrame({'Header1': [], 'Header2': [], 'Header3': []})
    expected_columns = ['Header1', 'Header2', 'Header3']
    assert extract_column_names(df) == expected_columns

def test_extract_column_names_empty_input():
    assert extract_column_names([]) == []
    assert extract_column_names({}) == []

def test_extract_column_names_dataframes_with_no_columns():
    df1 = pd.DataFrame()
    df2 = pd.DataFrame()
    assert extract_column_names([df1, df2]) == []
    assert extract_column_names({'s1': df1, 's2': df2}) == []
