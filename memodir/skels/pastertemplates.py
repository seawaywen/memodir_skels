
from random import choice
from memodir.skels.base import BaseTemplate, var
#from .base import BaseTemplate, var


class DjangoTemplate(BaseTemplate):

    vars = [
        var('version', 'Version (like 0.1)', default='0.1'),
        var('description', 'One-line description of the package'),
        var('long_description', 'Multi-line description (in reST)'),
        var('keywords', 'Space-separated keywords/tags'),
        var('author', 'Author name'),
        var('author_email', 'Author email'),
        var('url', 'URL of homepage'),
        var('license_name', 'License name'),
        var('zip_safe', 'True/False: if the package can be distributed as a .zip file',
            default=False),
    ]

    use_cheetah = True
    required_templates = []

    def check_vars(self, vars, command):
        if not command.options.no_interactive and \
           not hasattr(command, '_deleted_once'):
            del vars['package']
            command._deleted_once = True
        return super(DjangoTemplate, self).check_vars(vars, command)


class BuildoutProjectTemplate(BaseTemplate):
    _template_dir = 'templates/buildout_project'
    summary = 'A customized buildout dev environment project'
    required_templates = []
    use_cheetah = True
    
    vars = [
        var('django_version',
            'Django version to fetch, the default is 1.6.1', default='1.6.1'),
        var('django_project_name',
            'Name of the main Django project folder',
            default='project')
    ]

    def post(self, command, output_dir, vars):
        print "-----------------------------------------------------------"
        print "Generation finished"
        print "You probably want to run python bootstrap.py and then edit"
        print "buildout.cfg before running bin/buildout -v"
        print
        print "See README.txt for details"
        print "-----------------------------------------------------------"


