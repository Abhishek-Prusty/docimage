# Introduction
A library to process document images (with particular focus on Indic languages).

## Installation
- Install this library (Replace pip2 with pip3 as needed)
    - Latest release: `sudo pip2 install docimage -U`
    - Development copy: `sudo pip2 install git+https://github.com/vedavaapi/docimage@master -U`
    - [Web](https://pypi.python.org/pypi/docimage).

## Usage
- Please see the generated python sphynx docs in one of the following places:
    - [project page](https://vedavaapi.github.io/docimage/build/html/docimage.html).
    - http://docimage.readthedocs.io
    - under docs/_build/html/index.html
- Design considerations for data containers corresponding to the various submodules (such as books and annotations) are given below - or in the corresponding source files.

# For contributors
## Contact
Have a problem or question? Please head to [github](https://github.com/vedavaapi/docimage).

## Packaging
* ~/.pypirc should have your pypi login credentials.
```
python setup.py bdist_wheel
twine upload dist/* --skip-existing
```

## Document generation
- Sphynx html docs can be generated with `cd docs; make html`
- http://docimage.readthedocs.io/en/latest/docimage.html should automatically have good updated documentation - unless there are build errors.
