import os
from setuptools import setup, find_packages


def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''


setup(
    name='collab-staff-directory',
    version=__import__('staff_directory').__version__,
    author='CFPB',
    author_email='tech@cfpb.gov',
    packages=find_packages(),
    include_package_data=True,
    url='<Include Link to Project>',
    license='Public Domain',
    description=u'Staff Directory',
    classifiers=[
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Intended Audience :: Developers',
        'Programming Language :: Python',      
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Framework :: Django',
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
    ],
    long_description=read_file('README.md'),
    test_suite="runtests.runtests",
    zip_safe=False,
)
