import sys
import os
from networksecurity.logging import logger

class NetworkSecurityException(Exception):
    def __init__(self, error_message, error_details: sys):
        self.error_message = error_message
        try:
            _, _, exc_tb = error_details.exc_info()
            if exc_tb is not None:
                self.lineno = exc_tb.tb_lineno
                self.file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            else:
                self.lineno = "Unknown"
                self.file_name = "Unknown"
        except Exception as e:
            self.lineno = "Unknown"
            self.file_name = "Unknown"

    def __str__(self):
        return "Error occured in python script name [{0}] line number [{1}] error message [{2}]".format(
            self.file_name, self.lineno, str(self.error_message)
        )

# Optional: Testing the exception
if __name__ == '__main__':
    try:
        logger.logging.info("Enter the try block")
        a = 1 / 0
        print("This will not be printed", a)
    except Exception as e:
        raise NetworkSecurityException(e, sys)
