#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.pyson import Eval

__all__ = ['Configuration']


class Configuration(ModelSingleton, ModelSQL, ModelView):
    'Project Template Configuration'
    __name__ = 'project.template.configuration'
    default_template = fields.Property(fields.Many2One('project.work',
            'Default Template', domain=[
                ('company', 'in', [Eval('context', {}).get('company', 0)]),
                ('template', '=', True),
                ], required=True))
