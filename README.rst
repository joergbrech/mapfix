.. image:: images/presplash_b.png
  :align: center

MapFix
==========================

.. image:: https://readthedocs.org/projects/mapfix/badge/?version=latest
    :target: https://mapfix.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://travis-ci.com/joergbrech/mapfix.svg?token=3j1KXvuZPDDLeees2fes&branch=master
    :target: https://travis-ci.com/joergbrech/mapfix
.. image:: https://codecov.io/gh/joergbrech/mapfix/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/joergbrech/mapfix
    
MapFix lets you take photographs of maps and place markers on the image, whenever you know where you are. These markers are used to calibrate the image, so your current location based on your mobile phone's GPS device is dispayed in the image.

Add markers by double tap. A minimum of two markers is required. The more you add, the better the calibration will be.

.. list-table:: 

    * - .. figure:: images/Screenshot_03.png

      - .. figure:: images//Screenshot_02.png

      - .. figure:: images/Screenshot_06.png



Features
--------

* Corrects for orientation, scale and perspective
* Many different map projections
* Modify/Add/Delete calibration markers
* Recalibrate manually
* Lock a calibrated map

Experimental 
------------
MapFix is in experimantal state and is currently available in the Play Store for registered alpha testers. 
If you are interested, send me your google username and I will add you to the list of alpha testers!

Contributing
------------

Contributions in the form of issues or PRs are more than welcome!

Requirements
------------

To run MapFix on Windows, OSX or Linux, you need the following python packages: `kivy`, `click`, `piexif`, `pillow`, `unidecode`, `exifread`, `numpy`, `pyproj` and `plyer`. These will automatically be installed when you setup MapFix.

Depending on the features that you want to use, you do require additional libs though.

* `pytest`_ - implement readable tests without boilerplate-code
* `pytest-cov`_ - generate an ``html`` coverage report
* `Sphinx`_ - generate a readable ``html`` documentation
* `Buildozer`_ - deploy your app to an Android mobile device


Installation
------------

Clone the repository:

.. code-block:: bash

    $ git clone https://github.com/joergbrech/mapfix.git
    $ cd mapfix

Create a new virtual environment. Given that you are using `virtualenvwrapper`_:

.. code-block:: bash

    $ mkvirtualenv -a $(pwd) --system-site-packages mapfix

.. note:: If you prefer to set up a fresh env, feel free to omit the according option.
    Chances are that you want to use your systems `Kivy`_ including all its dependencies such as `Cython`_.

Install the app package in "editable" mode:

.. code-block:: bash

    $ python setup.py develop


Usage
-----

Launch the app via:

.. code-block:: bash

    $ mapfix

Run the `pytest`_ test suite:

.. code-block:: bash

    $ make test

Generate an ``html`` coverage report:

.. code-block:: bash

    $ make coverage

Generate `Sphinx`_ ``html`` documentation:

.. code-block:: bash

    $ make docs

Build an android apk with `Buildozer`_:

.. code-block:: bash

    $ make apk

Deploy the app to your android device with `Buildozer`_:

.. code-block:: bash

    $ make deploy


License
-------

Distributed under the terms of the `MIT license`_, MapFix is free and open source software


Issues
------

If you encounter any problems, please `file an issue`_ along with a detailed description.

----

This `Kivy`_ app was generated with `Cookiecutter`_ along with `@hackebrot`_'s `Cookiedozer`_ template.


.. _`@hackebrot`: https://github.com/hackebrot
.. _`Buildozer`: https://github.com/kivy/buildozer
.. _`Cookiecutter`: https://github.com/audreyr/cookiecutter
.. _`Cookiedozer`: https://github.com/hackebrot/cookiedozer
.. _`Cython`: https://pypi.python.org/pypi/Cython/
.. _`Kivy`: https://github.com/kivy/kivy
.. _`MIT License`: http://opensource.org/licenses/MIT
.. _`Sphinx`: http://sphinx-doc.org/
.. _`file an issue`: https://github.com/joergbrech/mapfix/issues
.. _`pytest-cov`: https://pypi.python.org/pypi/pytest-cov
.. _`pytest`: http://pytest.org/latest/
.. _`virtualenvwrapper`: https://virtualenvwrapper.readthedocs.org/en/latest/
