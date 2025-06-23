from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict

class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class with custom response format
    """
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.page_size),
            ('results', data)
        ]))

class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination for large datasets
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200

class SmallResultsSetPagination(PageNumberPagination):
    """
    Pagination for small datasets
    """
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20
