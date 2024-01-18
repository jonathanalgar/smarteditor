import logging
from io import StringIO

import nbformat
from nbformat.reader import NotJSONError


def is_valid_notebook(content):
    """
    Check if the given content is a valid Jupyter notebook.

    Args:
        content (str): The content of the notebook.

    Returns:
        bool: True if the content is a valid notebook, False otherwise.
    """
    try:
        nbformat.reads(content, as_version=4)
        return True
    except NotJSONError:
        return False


def keep_only_markdown_cells(notebook_content):
    """
    Filters out only the markdown cells from a Jupyter Notebook.

    Args:
        notebook_content (str): The content of the Jupyter Notebook.

    Returns:
        str: The modified content of the Jupyter Notebook with only markdown cells.
    """
    if not is_valid_notebook(notebook_content):
        raise ValueError("The content is not a valid Jupyter Notebook")

    notebook = nbformat.reads(notebook_content, as_version=4)
    markdown_cells = [cell for cell in notebook.cells if cell.cell_type == 'markdown']

    notebook.cells = markdown_cells

    logging.info("Kept only markdown cells in Jupyter Notebook")

    output_stream = StringIO()
    nbformat.write(notebook, output_stream)

    return output_stream.getvalue()
