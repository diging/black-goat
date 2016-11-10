REST API
========

BlackGoat exposes the following endpoints.

.. _authoritylist:

``/authority/``
---------------

``GET``
````````
Returns a list of known authority services.

.. code-block:: javascript

    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
             "id": 4,
             "added": "2016-11-09T21:27:26.955443Z",
             "updated": "2016-11-10T12:30:03.360530Z",
             "name": "Conceptpower",
             "namespace": null,
             "description": "",
             "configuration": "...",
             "added_by": 2,
             "builtin_identity_system": null
            },
            ...
        ]
    }


``POST``
````````
Register a new authority service.

.. list-table:: Accepted fields
   :widths: 10 5 10 35
   :header-rows: 1

   * - Property
     - Type
     - Required
     - Description
   * - ``name``
     - String
     - Yes
     - A (brief) name of the authority service. May be used for display.
   * - ``namespace``
     - String
     - Recommended
     - Highly recommended. If provided, will be used to match concepts that are
       registered without an explicit reference to an authority service.
   * - ``description``
     - String
     - No
     - A longer-form description of the service. Used for display.
   * - ``configuration``
     - String
     - Recommended
     - Must be a valid JSON document. This is necessary to take advantage of
       distributed search and validation functionality.

Should return ``201`` with the same representation of the authority service as
in :ref:`authoritydetail`.

.. _authoritydetail:

``/authority/{id}/``
---------------

``GET``
```````
