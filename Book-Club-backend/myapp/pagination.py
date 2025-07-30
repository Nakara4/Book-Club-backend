"""
Custom pagination classes for consistent API responses
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class with consistent response format for React frontend
    
    Response format:
    {
        "results": [...],
        "pagination": {
            "count": 100,
            "page": 1,
            "pages": 10,
            "page_size": 10,
            "has_next": true,
            "has_previous": false,
            "next": "http://...",
            "previous": null
        }
    }
    """
    page_size = 12  # Good for grid layouts (3x4, 4x3, 6x2, etc.)
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('results', data),
            ('pagination', OrderedDict([
                ('count', self.page.paginator.count),
                ('page', self.page.number),
                ('pages', self.page.paginator.num_pages),
                ('page_size', self.get_page_size(self.request)),
                ('has_next', self.page.has_next()),
                ('has_previous', self.page.has_previous()),
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link()),
            ]))
        ]))


class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination for endpoints that typically return large datasets
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('results', data),
            ('pagination', OrderedDict([
                ('count', self.page.paginator.count),
                ('page', self.page.number),
                ('pages', self.page.paginator.num_pages),
                ('page_size', self.get_page_size(self.request)),
                ('has_next', self.page.has_next()),
                ('has_previous', self.page.has_previous()),
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link()),
            ]))
        ]))


class SmallResultsSetPagination(PageNumberPagination):
    """
    Pagination for endpoints with smaller datasets or mobile-friendly views
    """
    page_size = 8
    page_size_query_param = 'page_size'
    max_page_size = 50
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('results', data),
            ('pagination', OrderedDict([
                ('count', self.page.paginator.count),
                ('page', self.page.number),
                ('pages', self.page.paginator.num_pages),
                ('page_size', self.get_page_size(self.request)),
                ('has_next', self.page.has_next()),
                ('has_previous', self.page.has_previous()),
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link()),
            ]))
        ]))


class SearchResultsPagination(PageNumberPagination):
    """
    Pagination specifically for search results
    """
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 50
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('results', data),
            ('pagination', OrderedDict([
                ('count', self.page.paginator.count),
                ('page', self.page.number),
                ('pages', self.page.paginator.num_pages),
                ('page_size', self.get_page_size(self.request)),
                ('has_next', self.page.has_next()),
                ('has_previous', self.page.has_previous()),
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link()),
            ]))
        ]))
