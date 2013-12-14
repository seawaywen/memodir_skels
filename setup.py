from setuptools import setup, find_packages


version = '0.1.0'

setup(name='memodir.skels',
      version=version,
      description="Paster templates for creating Buildout environment applications as eggs",
      long_description=open("README.rst").read() + "\n" +
                       open("CHANGES").read(),

      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Development Status :: 4 - Beta",
        "Environment :: Plugins",
        "Framework :: Paste",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Framework :: Django",
      ],
      keywords='',
      author='Kelvin Li',
      author_email='kelvin@memodir.com',
      url='http://www.memodir.com',
      license='BSD',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['memodir'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'PasteScript>=1.3',
          'Cheetah',
      ],
      entry_points="""
      [paste.paster_create_template]
      buildout_project = memodir.skels.pastertemplates:BuildoutProjectTemplate
      """,
      )
