
========================
zprocess |release|
========================

`Chris Billington <mailto:chrisjbillington@gmail.com>`_, |today|


.. contents::
    :local:

A set of utilities for multiprocessing using zeromq. Includes process creation and
management, output redirection, message passing, inter-process locks, logging, and a
process-tree-wide event system.

`View on PyPI <http://pypi.python.org/pypi/zprocess>`_
| `View on GitHub <https://github.com/chrisjbillington/zprocess>`_
| `Read the docs <http://zprocess.readthedocs.org>`_

------------
Installation
------------

to install ``zprocess``, run:

.. code-block:: bash

    $ pip3 install zprocess

or to install from a clone of the repository:

.. code-block:: bash

    $ pip3 install .

zprocess requires Python 3.11 or newer.

---------------------
Possible improvements
---------------------

* An introduction, and worked examples.

----------------
Module reference
----------------


.. autoclass:: zprocess.clientserver.ZMQServer
    :members:

.. autoclass:: zprocess.clientserver.ZMQClient
    :members:

.. autofunction:: zprocess.utils.start_daemon


.. autofunction:: zprocess.process_tree.set_default_process_tree

.. autofunction:: zprocess.process_tree.get_default_process_tree
