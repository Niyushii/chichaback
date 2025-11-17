import graphene

class Upload(graphene.Scalar):
    '''Scalar para manejar archivos subidos vía GraphQL'''

    @staticmethod
    def serialize(value):
        return None

    @staticmethod
    def parse_literal(node):
        return None

    @staticmethod
    def parse_value(value):
        return value
