import pandas as pd
import pdfplumber
from docx import Document
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_excel(file_content, file_name):
    """
    Parses an Excel file (xls or xlsx) and returns a dictionary of DataFrames,
    where keys are sheet names and values are the corresponding DataFrames.
    """
    try:
        # Ensure file_content is a BytesIO buffer
        if not isinstance(file_content, io.BytesIO):
            file_content = io.BytesIO(file_content.getvalue())
            file_content.seek(0) # Reset buffer position after reading getvalue()

        xls = pd.ExcelFile(file_content)
        sheet_names = xls.sheet_names
        data_frames = {}
        for sheet_name in sheet_names:
            data_frames[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)
        logging.info(f"Successfully parsed Excel file: {file_name} with sheets: {', '.join(sheet_names)}")
        return data_frames
    except Exception as e:
        logging.error(f"Error parsing Excel file {file_name}: {e}")
        return {}

def parse_pdf(file_content, file_name):
    """
    Parses a PDF file and extracts tables into a list of DataFrames.
    """
    data_frames = []
    try:
        # Ensure file_content is a BytesIO buffer
        if not isinstance(file_content, io.BytesIO):
            file_content = io.BytesIO(file_content.getvalue())
            file_content.seek(0)

        with pdfplumber.open(file_content) as pdf:
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if tables:
                    for j, table_data in enumerate(tables):
                        if table_data: # Ensure table_data is not empty
                            df = pd.DataFrame(table_data[1:], columns=table_data[0]) # Use first row as header
                            df.attrs['source'] = f"Page_{i+1}_Table_{j+1}"
                            data_frames.append(df)
                else: # Fallback if extract_tables returns nothing
                    table = page.extract_table()
                    if table:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        df.attrs['source'] = f"Page_{i+1}"
                        data_frames.append(df)
                    else:
                        # If neither extract_tables() nor extract_table() finds anything on a page,
                        # log this. More advanced text extraction could be a future enhancement if needed.
                        logging.warning(f"No tables extracted using extract_tables() or extract_table() on page {i+1} of {file_name}.")

        if data_frames:
            logging.info(f"Successfully parsed PDF file: {file_name}, found {len(data_frames)} table(s).")
        else:
            logging.warning(f"No tables found in PDF file: {file_name}")
        return data_frames
    except Exception as e:
        logging.error(f"Error parsing PDF file {file_name}: {e}")
        return []

def parse_word(file_content, file_name):
    """
    Parses a Word document (.doc, .docx) and extracts tables into a list of DataFrames.
    """
    data_frames = []
    try:
        # Ensure file_content is a BytesIO buffer
        if not isinstance(file_content, io.BytesIO):
            file_content = io.BytesIO(file_content.getvalue())
            file_content.seek(0)
            
        doc = Document(file_content)
        for i, table in enumerate(doc.tables):
            rows_data = []
            for row in table.rows:
                rows_data.append([cell.text for cell in row.cells])
            
            if rows_data: # Ensure there is data to create a DataFrame
                df = pd.DataFrame(rows_data[1:], columns=rows_data[0]) # Use first row as header
                df.attrs['source'] = f"Table_{i+1}"
                data_frames.append(df)
        
        if data_frames:
            logging.info(f"Successfully parsed Word file: {file_name}, found {len(data_frames)} table(s).")
        else:
            logging.warning(f"No tables found in Word file: {file_name}")
        return data_frames
    except Exception as e:
        # python-docx might raise PackageNotFoundError for .doc files or other issues
        logging.error(f"Error parsing Word file {file_name}: {e}. This parser primarily supports .docx files.")
        return []
