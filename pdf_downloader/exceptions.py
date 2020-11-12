class OperatingSystemIncompatible(Exception):
    """Raised when the current OS is not from any of the following: Windows, Linux or Darwin (OS X)"""
    pass


class NoDownloadableContentFound(Exception):
    """Raised when no downloadble content found on the given URL"""
    pass


class NoPDFLinkFound(Exception):
    """Raised when the scraper can not find a link for PDF file"""
    pass


class CanNotCreateFolder(Exception):
    """raised when the scraper can not create a folder for storing the PDFs"""
    pass
