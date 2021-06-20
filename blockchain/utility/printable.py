class Printable:
    """
    Return a dictionary representation
    of a string
    """
    def __repr__(self):
        return str(self.__dict__)
