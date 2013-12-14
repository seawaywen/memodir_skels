__author__ = 'kelvin'

import os
from os.path import join, dirname, abspath
import sys

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.wsgi
from tornado.options import options, define, parse_command_line

import ConfigParser

import sqlite3

from qt.deploy.deploy import db


class ImproperlyConfigured(Exception):
    pass


def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = "Set the %s env variable" % var_name
        raise ImproperlyConfigured(error_msg)


ROOT = get_env_variable('ATRR_HOME')
IS_PROD = get_env_variable('ATRR_IS_PROD')

#TO-DO: how to integrate tornado into Django
# see http://geekscrap.com/2010/02/integrate-tornado-in-django/


def get_data_by_inst_name(inst_name):
    inst = db.query_inst_by_name(inst_name)
    values_info = dict()

    if inst is not None:
        _field_list = ['db_host', 'db_name', 'db_user', 'db_password', 'db_port', 'inst_app_port', 'inst_name']
        for field in _field_list:
            if getattr(inst, field) is not None:
                values_info[field] = getattr(inst, field)

    return values_info


def set_host_env():
    os.environ["DJANGO_SETTINGS_MODULE"] = "qt_host.settings.{0}".format("production" if IS_PROD else "local")


def set_env(values_dict):
    for k, v in values_dict.iteritems():
        os.environ[k] = str(v)
    os.environ["DJANGO_SETTINGS_MODULE"] = "qt_atrr.settings.{0}".format("production" if IS_PROD else "local")


def set_pid(inst_name):
    db.update_pid(inst_name, os.getpid())


def set_logger(inst_name):
    app_log_dir = join(join(ROOT, 'logs'), inst_name)

    options._options['logging'].set('info')
    options._options['log_file_prefix'].set(os.path.join(app_log_dir, 'tornado.log'))
    options._options['log_to_stderr'].set(False)

    tornado.options.parse_command_line()


def main(inst_name, is_for_host_manager=False):
    values_dict = get_data_by_inst_name(inst_name)

    #print (is_for_host_manager, is_debug)

    if is_for_host_manager:
        #print 'is_for_host_manager'
        set_host_env()
    else:
        #print 'is_for_app_server'
        set_env(values_dict)

    #print os.environ

    set_pid(inst_name)
    set_logger(inst_name)

    import django.core.handlers.wsgi
    wsgi_app = tornado.wsgi.WSGIContainer(django.core.handlers.wsgi.WSGIHandler())
    tornado_app = tornado.web.Application([
        ('.*', tornado.web.FallbackHandler, {
            'fallback': wsgi_app
        }),
    ])

    server = tornado.httpserver.HTTPServer(tornado_app)
    server.listen(values_dict['inst_app_port'], '0.0.0.0')
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    arg_list = []

    for arg in sys.argv:
        if arg == 'False':
            arg_list.append(False)
        elif arg == 'True':
            arg = True
            arg_list.append(True)
        else:
            arg_list.append(arg)

    #print arg_list[1:]

    if len(arg_list) <= 4:
        main(*arg_list[1:])
    else:
        raise ValueError('parameter number error')

