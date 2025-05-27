import logging
import os


def configure_logging():
    """
    Configure the logging system for the project management application.

    Sets up logging to write messages to a file named 'project_management.log' with a specified format.
    The logging level is set to INFO, capturing informational and higher-severity messages.
    """
    logging.basicConfig(
        level=logging.INFO,  # Set logging level to INFO
        format='%(asctime)s - %(levelname)s - %(message)s',  # Define log message format: timestamp, level, message
        handlers=[
            logging.FileHandler('project_management.log'),  # Output logs to a file
        ]
    )


# Define the path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(__file__), 'logic', 'project_management.db')
"""
str: The absolute path to the SQLite database file 'project_management.db' located in the 'logic' directory.
Constructed using the current file's directory to ensure portability.
"""