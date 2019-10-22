.. image:: data/images/logo_mapfix.png
  :align: center

Mapfix
==========================

.. image:: https://readthedocs.org/projects/mapfix/badge/?version=latest
    :target: https://mapfix.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://travis-ci.com/joergbrech/mapfix.svg?token=3j1KXvuZPDDLeees2fes&branch=master
    :target: https://travis-ci.com/joergbrech/mapfix
.. image:: https://codecov.io/gh/joergbrech/mapfix/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/joergbrech/mapfix
.. image:: https://play.google.com/intl/en_us/badges/static/images/badges/en_badge_web_generic.png
    :target: href='https://play.google.com/store/apps/details?id=org.mapfix.mapfix&pcampaignid=pcampaignidMKT-Other-global-all-co-prtnr-py-PartBadge-Mar2515-1
    :alt: Get it on Google Play
    
MapFix lets you take photographs of maps and place markers on the image, whenever you know where you are. These markers are used to callibrate the image, so your current location based on your mobile phone's GPS device is dispayed in the image.

Add markers by double tap. A minimum of two markers is required. The more you add, the better the calibration will be.


Features
--------

* Corrects for orientation, scale and perspective
* Many different map projects
* Modify/Add/Delete calibration points
* Recalibrate manually
* Lock a calibrated map


Requirements
------------

To run "Mapfix" you only need `Kivy`_.

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

Generate an ``html`` coverage report and open it:

.. code-block:: bash

    $ make coverage

Generate `Sphinx`_ ``html`` documentation and open it:

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

Distributed under the terms of the `MIT license`_, "Mapfix" is free and open source software


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
