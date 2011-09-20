# vim: et :
""" Middle class
    ============

    This module provides the class Middle which is placed between Nap and the
    XML-RPC class.
    
    For a detailed description of the API, see :doc:`nap`.
"""
import logging


class Middle:
    """ Class which is placed between the Nap and XML-RPC classes to
        do authorization and "convert" method arguments.
    """

    def __init__(self, nap):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initialising Middle")

        self.nap = nap


    #
    # SCHEMA FUNCTIONS
    #
    def add_schema(self, args):
        """ Add a new network schema.
        """

        return self.nap.add_schema(args.get('attr'))


    def remove_schema(self, args):
        """ Removes a schema.
        """

        self.nap.remove_schema(args.get('schema'))


    def list_schema(self, args=None):
        """ List schemas.
        """

        return self.nap.list_schema(args.get('schema'))


    def edit_schema(self, args):
        """ Edit a schema.
        """

        self.nap.edit_schema(args.get('schema'), args.get('attr'))


    def search_schema(self, args):
        """ Search for schemas.

            The 'query' input is a specially crafted dict/struct which
            permits quite flexible searches.
        """

        return self.nap.search_schema(args.get('query'), args.get('search_options'))


    def smart_search_schema(self, args):
        """ Perform a smart search.

            The smart search function tries to extract a query from a text
            string. This query is then passed to the search_prefix function,
            which performs the actual search.
        """

        return self.nap.smart_search_schema(args.get('query_string'), args.get('search_options'))


    #
    # POOL FUNCTIONS
    #
    def add_pool(self, args):
        """ Add a pool.
        """

        return self.nap.add_pool(args.get('schema'), args.get('attr'))


    def remove_pool(self, args):
        """ Remove a pool.
        """

        self.nap.remove_pool(args.get('schema'), args.get('pool'))


    def list_pool(self, args):
        """ List pools.
        """

        return self.nap.list_pool(args.get('schema'), args.get('pool'))


    def edit_pool(self, args):
        """ Edit pool.
        """

        return self.nap.edit_pool(args.get('schema'), args.get('pool'), args.get('attr'))


    def search_pool(self, args):
        """ Search for pools.

            The 'query' input is a specially crafted dict/struct which
            permits quite flexible searches.
        """

        return self.nap.search_pool(args.get('schema'), args.get('query'), args.get('search_options'))


    def smart_search_pool(self, args):
        """ Perform a smart search.

            The smart search function tries to extract a query from a text
            string. This query is then passed to the search_prefix function,
            which performs the actual search.
        """

        return self.nap.smart_search_pool(args.get('schema'), args.get('query_string'), args.get('search_options'))


    #
    # PREFIX FUNCTIONS
    #


    def add_prefix(self, args):
        """ Add a prefix.
        """

        return self.nap.add_prefix(args.get('schema'), args.get('attr'), args.get('args'))



    def list_prefix(self, args):
        """ List prefixes.
        """

        return self.nap.list_prefix(args.get('schema'), args.get('prefix'))



    def edit_prefix(self, args):
        """ Edit prefix.
        """

        return self.nap.edit_prefix(args.get('schema'), args.get('prefix'), args.get('attr'))



    def remove_prefix(self, args):
        """ Remove a prefix.
        """

        return self.nap.remove_prefix(args.get('schema'), args.get('prefix'))



    def search_prefix(self, args):
        """ Search for prefixes.

            The 'query' input is a specially crafted dict/struct which
            permits quite flexible searches.
        """

        return self.nap.search_prefix(args.get('schema'), args.get('query'), args.get('search_options'))



    def smart_search_prefix(self, args):
        """ Perform a smart search.

            The smart search function tries to extract a query from a text
            string. This query is then passed to the search_prefix function,
            which performs the actual search.
        """

        return self.nap.smart_search_prefix(args.get('schema'), args.get('query_string'), args.get('search_options'))



    def find_free_prefix(self, args):
        """ Find a free prefix.
        """

        return self.nap.find_free_prefix(args.get('schema'), args.get('args'))
