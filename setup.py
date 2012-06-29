# -*- coding:utf-8 -*-
from distutils.core import setup

setup(
    name = 'SubHub',
    version = '0.1.0',
    author = 'Ivan Sagalaev',
    author_email = 'Maniac@SoftwareManiacs.Org',
    packages = [
        'subhub',
        'subhub.management',
        'subhub.management.commands',
    ],
    url = 'https://launchpad.net/subhub',
    license = 'LICENSE.txt',
    description = 'A simple personal PSHB hub for use in Django projects for your own blog. Doesn\'t serve as a public hub for publishers, hence just "SubHub".',
    long_description = open('README.txt').read(),
)
