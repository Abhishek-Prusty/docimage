# Introduction
A library to process document images (with particular focus on Indic languages).

## Usage
- Please see the generated python sphynx docs in one of the following places:
    - [project page](https://sanskrit-coders.github.io/docimage/build/html/docimage.html).
    - http://docimage.readthedocs.io
    - under docs/_build/html/index.html
- Design considerations for data containers corresponding to the various submodules (such as books and annotations) are given below - or in the corresponding source files.

# For contributors
## Contact
Have a problem or question? Please head to [github](https://github.com/sanskrit-coders/docimage).

## Packaging
* ~/.pypirc should have your pypi login credentials.
```
python setup.py bdist_wheel
twine upload dist/* --skip-existing
```

## Document generation
- Sphynx html docs can be generated with `cd docs; make html`
- http://docimage.readthedocs.io/en/latest/docimage.html should automatically have good updated documentation - unless there are build errors.
