import logging
from optparse import OptionParser
from logutils.colorize import ColorizingStreamHandler

__author__ = 'ericqu'
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(ColorizingStreamHandler())


def setEnv(prjName):
    os.environ['project_name'] = prjName
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qt_atrr.settings.production")


def createTR():
    from home.models import TestRun, Owner

    logger.debug(TestRun.objects.all())
    owner, isCreated = Owner.objects.get_or_create(name='Benoit Gennart')
    tr, isCreated = TestRun.objects.get_or_create(
        startDate="2011-06-01 12:00:00",
        endDate="2012-06-22 12:00:00",
        name="IMS5B-B1",
        reference="",
        lifeCycleTestingPhase="Development",
        projectName="Test Prj",
        objectives="",
        overAllReleaseStatus="Not Tested",
        synopsis="IMS 5.11 Beta1",
        version="v0.1",
        owner=owner
    )
    return tr


def importRunConfig(tr, filePath):
    from home.models import RunConfig
    import csv
    a = __import__('import.views.ImportView')
    b = a()

    with open(filePath, 'rb+') as f:
        csvReader = csv.reader(f, skipinitialspace=True)
        for row in csvReader:
            RunConfig.objects.get_or_create(testRun=tr, definition=row[2])

    logger.debug(RunConfig.objects.all())


if __name__ == '__main__':
    usage = '''\
    [bin/python] database_op_example.py [options]

    Demonstrate how to use django objects update database.

    '''

    parser = OptionParser(usage=usage)

    parser.add_option("-p", "--project",
                      dest="prjName",
                      help="Indicate which project database you are going to update")

    parser.add_option("-f", "--path",
                      dest="path",
                      help="Indicate the csv file path to import")

    options, args = parser.parse_args()

    if options.prjName is None:
        logger.error("Must provide the project name with option -p [project name]")
    elif options.path is None:
        logger.error("Must provide the csv file path with option -f [absolute file path]")
    else:
        setEnv(options.prjName)
        importRunConfig(createTR(), options.path)