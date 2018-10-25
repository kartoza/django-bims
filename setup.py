import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
        name='django-bims',
        version='0.1',
        packages=find_packages(exclude=['tests', ]),
        include_package_data=True,
        license='MIT License',
        description='BIMS Project',
        long_description=README,
        url='http://bims.kartoza.com',
        author='Dimas Ciputra',
        author_email='dimas@kartoza.com',
        classifiers=[
            'Environment :: Web Environment',
            'Framework :: Django',
            'Framework :: Django :: 1.11',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',  # example license
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Topic :: Internet :: WWW/HTTP',
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        ],
        install_requires=[
            'Django==1.11.15',
            'django-allauth==0.35.0',
            'django-role-permissions==2.2.0',
            'markdown==2.6.11',
            'django-braces==1.9.0',
            'django-model-utils==1.4.0',
            'djangorestframework==3.7.7',
            'django-filter==1.1.0',
            'coreapi==2.3.3',
            'pygbif==0.2.0',
            'django-modelsdoc==0.1.9',
            'django-contact-us==0.4.1',
            'Pillow==5.1.0',
            'django-ordered-model==1.4.3',
            'django-haystack==2.8.1',
            'elasticsearch==5.0.1',
            'bibtexparser==1.0.1',
            'eutils==0.4.0',
            'habanero==0.3.0',
            'django-prometheus==1.0.14',
            'prometheus_client==0.2.0',
            'django-ckeditor==5.6.1',
        ],
        dependency_links=[
            'git+https://github.com/soynatan/django-easy-audit.git',
        ]
)
