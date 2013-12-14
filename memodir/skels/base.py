from paste.script import templates
from paste.script.command import BadCommand
from paste.script.templates import BasicPackage


var = templates.var


def get_var(vars, name):
    for var in vars:
        if var.name == name:
            return var
    else:
        raise ValueError("No such var: %r" % name)


class BaseTemplate(templates.Template):
    """Base template for all ZopeSkel templates"""
    required_templates = []
    use_cheetah = True

    vars = [
        var('title', 'Title (use a short question)', 'Title'),
        var('short_name', ('Short name use for filename '
                           '(leave blank to make it calculated)'),
            default='recipe'),
        var('author', 'Author name', default='John Doe'),
        var('keywords', 'Space-separated keywords/tags', 'tag1 tag2')
    ]
