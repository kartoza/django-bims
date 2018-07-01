# td_biblio exceptions
class BaseLoaderError(Exception):
    pass


class BibTeXLoaderError(BaseLoaderError):
    pass


class PMIDLoaderError(BaseLoaderError):
    pass


class DOILoaderError(BaseLoaderError):
    pass
