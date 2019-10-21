import sys
import os

from setuptools import setup, find_packages
import mapfix


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='mapfix',
    version=mapfix.__version__,
    author='Jan Kleinert',
    author_email='jan@kleinert-bonn.de',
    description='Use photographed maps with your phone\'s GPS device',
    long_description=read('README.rst'),
    license='MIT',
    keywords=(
        "Python, cookiecutter, kivy, buildozer, pytest, projects, project "
        "templates, example, documentation, tutorial, setup.py, package, "
        "android, touch, mobile, NUI"
    ),
    url='https://github.com/joergbrech/mapfix',
    install_requires=[
        'kivy>=1.8.0',
        'click',
        'piexif',
        'pillow',
        'unidecode',
        'exifread',
        'numpy',
        'pyproj',
        'plyer'
    ],
    zip_safe=False,
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'mapfix=mapfix.main:main'
        ]
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: X11 Applications',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Artistic Software',
        'Topic :: Multimedia :: Graphics :: Presentation',
        'Topic :: Software Development :: User Interfaces',
    ],
)
