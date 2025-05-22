# Scholarship Eligibility Checker

## Overview/Purpose
The Scholarship Eligibility Checker is a Streamlit web application designed to help identify students who might be receiving scholarships or benefits from multiple sources. It achieves this by comparing a primary client file (containing a list of students/applicants) against one or more database files (containing records of scholarship recipients from various schemes or institutions).

## Features
*   **Flexible File Uploads:**
    *   Supports client file uploads in Excel (.xlsx, .xls), PDF (.pdf), and Word (.doc, .docx) formats.
    *   Supports database file uploads in Excel (.xlsx, .xls) format (multiple files can be uploaded simultaneously).
*   **Automated Data Extraction:** Automatically extracts tabular data from the uploaded files.
*   **Interactive Column Selection:** Allows users to select 1 or 2 columns from the client file and from the aggregated database files to be used for matching.
*   **Smart Column Standardization:** Suggests standardized names for selected columns (e.g., mapping "Student Name" and "Applicant Name" to a common "name" field) to improve matching accuracy across diverse datasets.
*   **Advanced Matching Logic:**
    *   Performs exact string matching for high-confidence results.
    *   Employs fuzzy string matching (using RapidFuzz) to identify non-exact matches, useful for catching variations in names or data entry errors.
    *   Adjustable fuzzy matching threshold (0-100) to control sensitivity.
*   **Clear Results & Reporting:**
    *   Identifies potential duplicates and clearly indicates the source database file and sheet where a match was found.
    *   Provides a downloadable Excel report of the matching results, with each client entry marked as "Duplicate Found", "Not Found", or "Skipped (Empty Client Data)".
*   **User-Friendly Interface:**
    *   Previews of parsed data from client and database files before processing.
    *   Displays summary statistics of the matching process (total entries, duplicates found, etc.).
    *   Built with Streamlit for an interactive web-based experience.

## Tech Stack
*   **Python:** Core programming language.
*   **Streamlit:** For creating the interactive web application UI.
*   **pandas:** For data manipulation and analysis, especially handling tabular data.
*   **pdfplumber:** For extracting text and tables from PDF files.
*   **python-docx:** For extracting text and tables from Word (.docx) files.
*   **RapidFuzz:** For fast and efficient fuzzy string matching.
*   **openpyxl:** For reading and writing Excel (.xlsx) files (used by pandas).
*   **xlrd:** For reading older Excel (.xls) files (used by pandas).
*   **pytest:** For running automated unit tests (primarily for developers).

## Project Structure
```
scholarship_checker/
├── app.py                  # Main Streamlit application script
├── requirements.txt        # Python dependencies
├── src/                    # Source code for core logic
│   ├── __init__.py
│   ├── parsers.py          # File parsing utilities
│   ├── column_utils.py     # Column name standardization and cleaning
│   └── matcher.py          # Matching logic
├── tests/                  # Unit tests
│   ├── __init__.py
│   ├── test_column_utils.py
│   └── test_matcher.py     # Placeholder for matcher tests
└── data_samples/           # (Optional) Directory for sample/test files
```

## Setup and Installation
1.  **Clone the Repository (if applicable):**
    If you have cloned this project from a Git repository, navigate into the cloned directory. Otherwise, ensure you have all project files in a directory named `scholarship_checker`.

2.  **Navigate to Project Directory:**
    Open your terminal or command prompt and change to the `scholarship_checker` directory:
    ```bash
    cd path/to/scholarship_checker
    ```

3.  **Create a Python Virtual Environment (Recommended):**
    This keeps project dependencies isolated.
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    *   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```
    *   On Windows:
        ```bash
        venv\Scripts\activate
        ```

4.  **Install Dependencies:**
    With the virtual environment activated, install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## How to Run the Application
1.  Ensure you are in the `scholarship_checker` directory in your terminal.
2.  Ensure your Python virtual environment (e.g., `venv`) is activated.
3.  Run the Streamlit application using the following command:
    ```bash
    streamlit run app.py
    ```
4.  Streamlit will typically open the application automatically in your default web browser. If not, it will display a local URL (e.g., `http://localhost:8501`) that you can open manually.

## How to Use the Application
1.  **Upload Client File:**
    *   In the application's sidebar, use the "Upload Client File" widget to upload a single client file. Supported formats are Excel (.xlsx, .xls), PDF (.pdf), or Word (.doc, .docx).
    *   Wait for the application to parse the file. A success message and data previews (collapsible) will appear.
2.  **Upload Database Files:**
    *   In the sidebar, use the "Upload Database Excel Files" widget to upload one or more database Excel files (.xlsx, .xls).
    *   Wait for parsing. Success messages and data previews for each file/sheet will appear.
3.  **Select Columns for Matching:**
    *   **Client Columns:** Once the client file is parsed and data is shown, a multiselect widget will appear below its preview. Select one or two columns from your client file that you want to use for matching (e.g., "Student Name", "Roll Number"). Standardized name suggestions are provided.
    *   **Database Columns:** Similarly, after database files are parsed, select one or two columns from the aggregated list of all database columns. These are the columns that will be searched in the database files.
4.  **Adjust Fuzzy Threshold (Optional):**
    *   Use the slider labeled "Fuzzy Match Sensitivity" to set the desired threshold for fuzzy matching (default is 85). A higher value means stricter matching.
5.  **Run Matching:**
    *   Once files are uploaded and columns are selected for both client and database, the "Run Matching" button will become active. Click it to start the comparison process.
6.  **View Results:**
    *   After processing, a table of results will be displayed. This table includes all entries from your client file, along with a "status" column ("Duplicate Found", "Not Found", or "Skipped (Empty Client Data)").
    *   If a duplicate is found, the `matched_file` and `matched_sheet` columns will indicate its source.
    *   Summary statistics (total entries processed, number of duplicates, etc.) will also be shown.
7.  **Export Results:**
    *   Click the "Export Results to Excel" button to download an Excel file containing the full results table.

## Running Tests (For Developers)
Unit tests are included for some utility functions.
1.  Ensure you have installed the development dependencies, including `pytest` (it's listed in `requirements.txt`).
2.  Navigate to the root `scholarship_checker` directory in your terminal.
3.  Run the tests using the following command:
    ```bash
    pytest
    ```

## `data_samples` Directory
This directory is provided as a suggested location to store sample client and database files. You can use these for testing the application's functionality or for demonstration purposes. It is not directly used by the application logic but is good for organizing test data.

## Contributing
This project is primarily for demonstration. However, if it were an open project, contributions could follow standard practices like:
1.  Forking the repository.
2.  Creating a new branch for features or bug fixes.
3.  Writing tests for new functionality.
4.  Submitting a pull request.

## License
This project is currently unlicensed. You are free to use, modify, and distribute the code as per your needs. If a specific license is required, please add one.
