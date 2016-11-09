from setuptools import setup, find_packages
import flask_boost

entry_points = {
    "console_scripts": [
        "turbo = flask_boost.cli:main",
    ]
}

with open("requirements.txt") as f:
    requires = [l for l in f.read().splitlines() if l]

setup(
    name='Flask-Turbo-Boost',
    version=flask_boost.__version__,
    packages=find_packages(),
    include_package_data=True,
    description='Forked Flask-Boost - Flask application generator for boosting your development.',
    long_description=open('README.rst').read(),
    url='https://github.com/jingz/Flask-Boost',
    author='jingz',
    author_email='wsaryoo@gmail.com',
    license='MIT',
    keywords='flask rich-sample generator',
    install_requires=requires,
    entry_points=entry_points,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
