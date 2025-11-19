import graphene
from graphql.language import ast

class Upload(graphene.Scalar):

    @staticmethod
    def serialize(value):
        return None

    @staticmethod
    def parse_literal(node):
        if isinstance(node, ast.StringValue):
            return node.value
        return None

    @staticmethod
    def parse_value(value):
        return value
