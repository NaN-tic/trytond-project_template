#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateTransition, Button

__all__ = ['Work', 'CreateFromTemplateStart', 'CreateFromTemplate']

__metaclass__ = PoolMeta


class Work:
    'Work Effort'
    __name__ = 'project.work'
    template = fields.Boolean('Template')
    percentage = fields.Float('Percentage',
        states={
            'invisible': Eval('type') != 'task',
            }, depends=['type'])

    @staticmethod
    def default_percentage():
        return 0.0

    @classmethod
    def create(cls, vlist):
        works = super(Work, cls).create(vlist)
        to_update = []
        for work in works:
            if work.parent and work.parent.template and not work.template:
                to_update.append(work)
        if len(to_update) > 0:
            cls.write(to_update, {'template': True})
        return works

    @classmethod
    def write(cls, works, values):
        transaction = Transaction()
        context = transaction.context
        if 'template' in values and not context.get('template', False):
            to_update = cls.search([
                    ('parent', 'child_of', [w.id for w in works]),
                    ('active', '=', True),
                    ]) + works

            with transaction.set_context(template=True):
                cls.write(to_update, {'template': values['template']})
            del values['template']
        return super(Work, cls).write(works, values)

    @classmethod
    def create_from_template(cls, works, name, effort):
        TimesheetWork = Pool().get('timesheet.work')
        transaction = Transaction()
        context = transaction.context
        new_works = []
        for work in works:
            with Transaction().set_context(template=True):
                new_work, = cls.copy([work])
                TimesheetWork.write([new_work.work], {'name': name})
                new_work.work.name = name
                new_work.template = False
                if context.get('party'):
                    new_work.party = context.get('party')
                if context.get('address'):
                    new_work.party_address = context.get('address')
                if len(work.children) == 0:
                    new_work.effort = effort
                new_work.save()
                new_works.append(new_work)
                for child in work.children:
                    new_child, = cls.copy([child])
                    new_child.effort = (child.percentage * effort) / 100.0
                    new_child.template = False
                    new_child.parent = new_work
                    new_child.save()
        return new_works


class CreateFromTemplateStart(ModelView):
    'Create From Template Start'
    __name__ = 'project_template.create_from_template_start'

    name = fields.Char('Name', help='Name of the new project/task to create.',
        required=True)
    effort = fields.Float('Effort', help='Total effort of the project/task.',
        required=True)


class CreateFromTemplate(Wizard):
    'Create From Template'
    __name__ = 'project_template.create_from_template'

    start = StateView('project_template.create_from_template_start',
        'project_template.create_from_template_start', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create Project', 'creatework', 'tryton-ok', default=True),
            ])
    creatework = StateTransition()

    def transition_creatework(self):
        Work = Pool().get('project.work')

        works = Work.browse(Transaction().context['active_ids'])
        Work.create_from_template(works, self.start.name,
            self.start.effort)
        return 'end'
