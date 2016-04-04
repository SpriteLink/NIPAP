
class NipapError(Exception):
    """ NIPAP base error class.
    """

    error_code = 1000


class NipapInputError(NipapError):
    """ Erroneous input.

        A general input error.
    """

    error_code = 1100


class NipapMissingInputError(NipapInputError):
    """ Missing input.

        Most input is passed in dicts, this could mean a missing key in a dict.
    """

    error_code = 1110


class NipapExtraneousInputError(NipapInputError):
    """ Extraneous input.

        Most input is passed in dicts, this could mean an unknown key in a dict.
    """

    error_code = 1120


class NipapNoSuchOperatorError(NipapInputError):
    """ A non existent operator was specified.
    """

    error_code = 1130


class NipapValueError(NipapError):
    """ Something wrong with a value

        For example, trying to send an integer when an IP address is expected.
    """

    error_code = 1200


class NipapNonExistentError(NipapError):
    """ A non existent object was specified

        For example, try to get a prefix from a pool which doesn't exist.
    """

    error_code = 1300


class NipapDuplicateError(NipapError):
    """ The passed object violates unique constraints

        For example, create a VRF with a name of an already existing one.
    """

    error_code = 1400
