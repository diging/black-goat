REST API
========

BlackGoat exposes the following endpoints.

.. _authoritylist:

``/authority/``
---------------

``GET``
````````
Returns a list of known authority services.

Sample Response
...............

.. code-block:: javascript

    {
        "count": 2,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 6,
                "added_by": {
                    "username": "erickpeirson",
                    "email": ""
                },
                "builtin_identity_system": {
                    "id": 2,
                    "name": "builtin:VIAF"
                },
                "added": "2016-11-15T20:55:02.682300Z",
                "updated": "2016-11-15T20:55:12.030762Z",
                "name": "VIAF",
                "namespace": "http://viaf.org/viaf/",
                "description": "Virtual Internet Authority File"
            },
            {
                "id": 7,
                "added_by": {
                    "username": "erickpeirson",
                    "email": ""
                },
                "builtin_identity_system": {
                    "id": 3,
                    "name": "builtin:Conceptpower"
                },
                "added": "2016-11-15T20:55:44.522994Z",
                "updated": "2016-11-15T20:55:50.012521Z",
                "name": "Conceptpower",
                "namespace": "http://www.digitalhps.org/",
                "description": "Conceptpower online authority service"
            }
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
--------------------

``GET``
```````
Returns details about an authority service. This view includes the JSON
configuration document for the service.

Sample Response
...............

.. code-block:: javascript

    {
        "id": 7,
        "added_by": {
            "username": "erickpeirson",
            "email": ""
        },
        "builtin_identity_system": {
            "id": 3,
            "name": "builtin:Conceptpower"
        },
        "added": "2016-11-15T20:55:44.522994Z",
        "updated": "2016-11-15T20:55:50.012521Z",
        "name": "Conceptpower",
        "namespace": "http://www.digitalhps.org/",
        "description": "Conceptpower online authority service",
        "configuration": "{\r\n    \"name\": \"Conceptpower\", ... }"
    }


.. _conceptlist:

``/concept/``
-------------

``GET``
```````
Returns a list of known concepts.

The following parameters can be used to filter/sort the results.

.. list-table:: Accepted parameters
   :widths: 10 5 10 35
   :header-rows: 1

   * - Property
     - Type
     - Required
     - Description
   * - ``name``
     - String
     - No
     - Returns only concepts whose ``name`` contains (case-insensitive) the
       provided value.
   * - ``identifier``
     - String
     - No
     - Returns only concepts whose ``identifier`` matches the passed value. This
       should (in theory) return only one result.
   * - ``concept_type``
     - String
     - No
     - Returns only concepts of a specific type (by type ``identifier``).
   * - ``added_by``
     - String
     - No
     - Returns only concepts added by a specific user (by ``username``).
   * - ``authority``
     - Int
     - No
     - Return only concepts from a specific authority (by ID).
   * - ``o``
     - String
     - No
     - Order by a specific field. Recognizes ``name``, ``-name``,
       ``concept_type``, and ``-concept_type``.
   * - ``page``
     - Int
     - No
     - Page number (starting at 1).


Sample Response
...............

.. code-block:: javascript

    {
        "count": 19,
        "next": "http://127.0.0.1:8000/concept/?page=2",
        "previous": null,
        "results": [
            {
                "id": 55,
                "added_by": {
                    "username": "erickpeirson",
                    "email": ""
                },
                "authority": {
                    "id": 6,
                    "name": "VIAF"
                },
                "added": "2016-11-15T20:56:30.502749Z",
                "updated": "2016-11-15T20:56:30.502820Z",
                "name": "",
                "identifier": "viaf:personal",
                "local_identifier": null,
                "description": null,
                "concept_type": null
            },
            ...
            {
                "id": 64,
                "added_by": {
                    "username": "erickpeirson",
                    "email": ""
                },
                "authority": {
                    "id": 6,
                    "name": "VIAF"
                },
                "added": "2016-11-15T20:56:30.686089Z",
                "updated": "2016-11-15T20:56:30.686124Z",
                "name": "Bradshaw, Rita, 1950-",
                "identifier": "http://viaf.org/viaf/66597118",
                "local_identifier": "66597118",
                "description": "Bradshaw, Rita, 1950-",
                "concept_type": 55
            }
        ]
    }


``POST``
````````
Register a new concept.

.. list-table:: Accepted parameters
   :widths: 10 5 10 35
   :header-rows: 1

   * - Property
     - Type
     - Required
     - Description
   * - ``name``
     - String
     - Yes
     - The primary human-readable representation of the concept.
   * - ``identifier``
     - String
     - Yes
     - This should be a valid URI for the concept.
   * - ``local_identifier``
     - String
     - Yes
     - An identifier used internally by the authority service to identify this
       concept.
   * - ``description``
     - String
     - No
     - A longer-form description of the concept. Used for display.
   * - ``authority``
     - Int
     - Yes
     - The ID of the authority service to which this concept belongs.

Should return ``201`` with the same representation of the authority service as
in :ref:`conceptdetail`.

.. _conceptdetail:

``/concept/{id}/``
------------------

``GET``
```````

Returns details about a concept.

.. code-block:: javascript

    {
        "id": 56,
        "added_by": {
            "username": "erickpeirson",
            "email": ""
        },
        "authority": {
            "id": 6,
            "name": "VIAF"
        },
        "added": "2016-11-15T20:56:30.525892Z",
        "updated": "2016-11-15T20:56:30.525930Z",
        "name": "Bradshaw Isherwood, Christopher William, 1904-1986",
        "identifier": "http://viaf.org/viaf/76317308",
        "local_identifier": "76317308",
        "description": "Bradshaw Isherwood, Christopher William, 1904-1986",
        "concept_type": 55
    }


.. _identical:

``/identical/``
---------------

Returns a list of concepts that share identity relations with a specific
concept.





Sample Response
................

``/identical/?identifier=http://www.digitalhps.org/concepts/72ec32b4-2a20-4d26-ab8f-a173f067542d``

.. code-block:: javascript

    {
        "results":[
            {
                "id":56,
                "added_by":{
                    "username":"erickpeirson",
                    "email":""
                },
                "authority":{
                    "id":6,
                    "name":"VIAF"
                },
                "added":"2016-11-15T20:56:30.525892Z",
                "updated":"2016-11-15T20:56:30.525930Z",
                "name":"Bradshaw Isherwood, Christopher William, 1904-1986",
                "identifier":"http://viaf.org/viaf/76317308",
                "local_identifier":"76317308",
                "description":"Bradshaw Isherwood, Christopher William, 1904-1986",
                "concept_type":55
            },
            {
                "id":69,
                "added_by":{
                    "username":"erickpeirson",
                    "email":""
                },
                "authority":{
                    "id":7,
                    "name":"Conceptpower"
                },
                "added":"2016-11-15T20:56:30.989382Z",
                "updated":"2016-11-15T20:56:30.989422Z",
                "name":"Anthony D. Bradshaw",
                "identifier":"http://www.digitalhps.org/concepts/72ec32b4-2a20-4d26-ab8f-a173f067542d",
                "local_identifier":"http://www.digitalhps.org/concepts/72ec32b4-2a20-4d26-ab8f-a173f067542d",
                "description":null,
                "concept_type":null
            }
        ]
    }
