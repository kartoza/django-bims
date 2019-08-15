from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

PMID_REGEX = '^-?\d+\Z'
pmid_validator = RegexValidator(
    PMID_REGEX,
    _("One (or more) PMID is not valid"),
    'invalid'
)

DOI_REGEX = '(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?!["&\'<>])\S)+)'
doi_validator = RegexValidator(
    DOI_REGEX,
    _("One (or more) DOI is not valid"),
    'invalid'
)


class BibliographyFormatValidator(object):
    """Checking bibliography format identifier validator.
    Used for checking format of doi and pmid
    """

    @staticmethod
    def doi_format_validation(doi):
        """ Validate doi format
        :param doi: doi input
        :type doi:str
        """
        try:
            doi_validator(doi)
        except ValidationError:
            raise ValidationError('%s is not doi valid format' % doi)

    @staticmethod
    def pmid_format_validation(pmid):
        """ Validate pmid format
        :param pmid: pmid input
        :type pmid:str """
        try:
            pmid_validator(pmid)
        except ValidationError:
            raise ValidationError('%s is not pmid valid format' % pmid)
