Authority Service Description
=============================

BlackGoat can query remote authority services that expose RESTful APIs. You can
tell BlackGoat how to query an API using a configuration document. This page
describes the convention for writing a service configuration document that
BlackGoat can understand.

The current version of BlackGoat supports public APIs only. Methods like
:ref:`create` will presumably require some form of authentication, so this
specification will be extended in the near future to support various
authentication schemes.

Overview
--------
A service configuration document is a valid JSON document that describes what
methods the service exposes, and how to use those methods.

There are several core :ref:`special` that (ideally) each authority service
will provide and describe, including :ref:`getmethod` and :ref:``searchmethod``.


.. _template:

Template
--------
Many properties of a configuration will use special template declarations to
describe how an endpoint should be called.

``{}`` - Curly braces can be used to indicate where parameters should be
inserted. There are some global variables (e.g. ``endpoint``) that are
available in any template. For method paths, variable names will be
dereferenced against the ``parameters`` defined for that method.


Top-level Properties
--------------------
The following properties should be included at the top level of the document.

.. list-table:: Top-level properties
   :widths: 10 5 10 35
   :header-rows: 1

   * - Property
     - Type
     - Required
     - Description
   * - ``name``
     - String
     - No
     - A (brief) name of the authority service. May be used for display.
   * - ``description``
     - String
     - No
     - A free-form description of the service. May be used for display.
   * - ``documentation``
     - String
     - Recommended
     - The location of human-readable documentation for the service.
   * - ``endpoint``
     - String
     - Yes
     - The root endpoint of the service API. This property will be used to build
       requests, and can be referenced in path templates as ``{endpoint}``.
   * - ``methods``
     - Array
     - Yes
     - This property contains all of the :ref:`methods` offered by the service.


Example
```````

.. code-block:: javascript

    {
        "name": "Conceptpower",
        "description": "Conceptpower authority service",
        "documentation": "http://diging.github.io/conceptpower",
        "endpoint": "http://chps.asu.edu/conceptpower/rest",
        "methods": [...]
    }


.. _methods:

Method Descriptions
-------------------
A service configuration can describe an unlimited number of methods. Each method
is represented as an object in the top-level :ref:`methods` property. Each
method should contain the properties shown below. There are several
:ref:`special` whose descriptions, if included, must conform to some additional
constraints.

.. list-table:: General method properties
   :widths: 10 5 10 35
   :header-rows: 1

   * - Property
     - Type
     - Required
     - Description
   * - ``name``
     - String
     - Yes
     - An Unix-name for the method.
   * - ``description``
     - String
     - No
     - A free-form description of the method. Used for display.
   * - ``path``
     - :ref:`template`
     - Yes
     - The location of the method interface relative to ``endpoint``. This can
       include parameters described in ``parameters`` (the name provided in
       the ``send`` parameter should be used).
   * - ``method``
     - String
     - Yes
     - This should be the name of an HTTP method, e.g. "GET", "POST", "PUT",
       etc.
   * - :ref:`parameters`
     - Array
     - No
     - If the method accepts specific parameters, they should be defined here.
   * - :ref:`response`
     - Object
     - Yes
     - Describes how to interpret the response from the method.


Example
```````

.. code-block:: javascript

   {
       ...
       "methods": [
           {
               "name": "get",
               "method": "GET",
               "path": "{endpoint}/Concept",
               "parameters": [ ... ],
               "response": { ... }
           },
       ]
   }


.. _parameters:

``parameters``
```````````````
The ``parameters`` property should contain descriptions of any parameters that
should be passed to the method. Any parameters not used to render the
``path`` template will be passed in the payload of the request.

Each object in ``parameters`` should include the following properties:

.. list-table:: Properties for parameters
   :widths: 10 5 10 35
   :header-rows: 1

   * - Property
     - Type
     - Required
     - Description
   * - ``accept``
     - String
     - Yes
     - The name of the parameter exposed to BlackGoat. If the method is one of
       the special methods, the value of this property may be constrained.
       May also be used for display purposes.
   * - ``send``
     - String
     - Yes
     - The name of the parameter sent to the method. If the parameter is used
       in the ``path`` template, this is the name that will be exposed.
       Otherwise, this will be used as the parameter name in the request
       payload.
   * - ``required``
     - Boolean
     - No
     - If not provided, defaults to ``false``.


Example
.......

.. code-block:: javascript

    ...
    "parameters": [
        {
            "accept": "id",
            "send": "sendid",
            "required": true
        }
        ...
    ],
    ...


.. _response:

``response``
```````````````
The ``response`` property should describe how to parse the response returned
by the service.

The following properties should be included:

.. list-table:: Properties for response
   :widths: 10 5 10 35
   :header-rows: 1

   * - Property
     - Type
     - Required
     - Description
   * - ``type``
     - String
     - Yes
     - Should be ``xml`` (implemented) or ``json`` (coming soon).
   * - ``path``
     - :ref:`paths`
     - No
     - Describes the starting point for parsing data in the response document.
       If not provided, paths in the individual response parameters will be
       assumed to start at the root of the document.
   * - ``namespaces``
     - Array
     - No
     - Any namespaces used in the response document should be provided here.
       Each namespace should be an object with two parameters: ``prefix``
       (used in parameter paths) and ``namespace``. For example:

       .. code-block:: javascript

           "namespaces": [
               {
                   "prefix": "digitalHPS",
                   "namespace": "http://www.digitalhps.org/"
               },
               ...
           ]

   * - ``parameters``
     - Array
     - Yes
     - Each object in ``parameters`` should contain two properties: ``name``,
       which will be the data key exposed to BlackGoat, and ``path``, which
       should describe where in the response to find the corresponding value.
       See :ref:`paths` for details.
       For example:

       .. code-block:: javascript

           "parameters": [
               ...
               {
                   "name": "concept_type",
                   "path": "digitalHPS:type[type_uri]"
               },
               ...
            ]


.. _paths:

Path
----
When interpreting a response from an API, BlackGoat will use the paths defined
in the method's ``parameters`` property to extract specific pieces of
information.

* ``/`` - Parts (levels) of a path should be separated by the forward slash.
* ``:`` - If ``namespaces`` are defined (see below), the colon should be used
  to explicitly declare the namespace of each part of a path. For example,
  the path ``digitalHPS:conceptEntry/digitalHPS:lemma`` refers to the ``lemma``
  element inside the ``conceptEntry`` element, both of which belong to the
  ``digitalHPS`` namespace.
* ``[]`` - If the value of interest resides in an attribute of the focal
  element, that attribute can be referenced using square braces. Note that this
  only applies to the deepest (last) element in the path. This really only
  applies to XML response. This should come before the ``*`` and ``|``
  operators.
* ``*`` - The asterisk following an element name indicates that there may be
  multiple elements that match the path at a given level. If provided in a
  parameter description, multiple values will be returned for that field. If
  provided in the base ``path`` for a ``response``, then multiple results will
  be extracted. The ``*`` should come at the end of the element name, but before
  the ``|`` operator.
* ``|`` - If provided after on the last element of the path, indicates that the
  value in the target element should be separated into multiple values using
  a specific delimiter. For example, ``names|,`` indicates that the value of
  the ``names`` element should be split on any commas.

Example
```````

Given the following document:

.. code-block:: xml

   <root>
       <things>
           <thing>
               <age real-age="54">43</age>
               <names>Bob, Robert, Rob</name>
           </thing>
           <thing>
               <age real-age="4">5</age>
               <names>Josephine, Jo</name>
           </thing>
        </things>
    </root>


This configuration...

.. code-block:: javascript

   "response": {
        "type": "xml",
        "path": "root/things/thing*",
        "parameters": [
            {
                "name": "monikers",
                "path": "names|,"
            },
            {
                "name": "age",
                "path": "age[real-age]"
            }
        ]
   }


...will extract the following data:

.. code-block:: javascript

   [
        {
            "monikers": [
                "Bob",
                "Robert",
                "Rob"
            ],
            "age": "54"
        },
        {
            "monikers": [
                "Jo",
                "Josephine"
            ],
            "age": "4"
        }
   ]


.. _special:

Special Methods
---------------

There are a few methods that most authority services will be expected to
provide. Each of these methods has some specific constraints.

.. _getmethod:

``get``
```````
The ``get`` method should yield a data object that represents a single
concept. The configuration for this method **must**...

* accept a parameter called ``id``;
* yield the parameter ``name``.

It **may** also yield the parameters ``description``, ``concept_type``, and
``identities``.

If ``concept_type`` is provided, its value **must** be an URI of a type concept.

If ``identities`` is provided, the values **must** be URIs of other concepts to
which the focal concept is identical. These will be used to automatically
generate identity statements.

.. _searchmethod:

``search``
``````````
The ``search`` method should yield an array of data objects, each of which
represents a single concept. The configuration for this method **must**...

* accept a parameter called ``q``;
* yield multiple results, each of which has the parameters ``name`` and
  ``identifier``.

It **may** also accept additional parameters.

Each result **may** also contain the parameters ``description``,
``concept_type``, and ``identities``.

If ``concept_type`` is provided, its value **must** be an URI of a type concept.

If ``identities`` is provided, the values **must** be URIs of other concepts to
which the focal concept is identical. These will be used to automatically
generate identity statements.

.. _create:

``create``
``````````
The ``create`` method should accept data that will be used to generate a new
concept in the authority system.

The configuration for this method **must**...

* accept the parameter``name``;
* yield a single data object with the parameters ``name`` and ``identifier``.

It **may** accept additional parameters, such as ``description`` and
``concept_type``.

It **may** also yield the parameters ``description``, ``concept_type``, and
``identities``.

If ``concept_type`` is provided, its value **must** be an URI of a type concept.

If ``identities`` is provided, the values **must** be URIs of other concepts to
which the focal concept is identical. These will be used to automatically
generate identity statements.

Full Example
------------
Here is a full configuration for the `Conceptpower API
<http://diging.github.io/conceptpower/>`_, with ``get`` and ``search`` methods.

.. code-block:: javascript

    {
        "name": "Conceptpower",
        "description": "Conceptpower authority service",
        "documentation": "http://diging.github.io/conceptpower",
        "endpoint": "http://chps.asu.edu/conceptpower/rest",
        "methods": [
            {
                "name": "get",
                "method": "GET",
                "path": "{endpoint}/Concept",
                "parameters": [
                    {
                        "accept": "id",
                        "send": "sendid",
                        "required": true
                    }
                ],
                "response": {
                    "type": "xml",
                    "path": "digitalHPS:conceptEntry",
                    "namespaces": [
                        {
                            "prefix": "digitalHPS",
                            "namespace": "http://www.digitalhps.org/"
                        }
                    ],
                    "parameters": [
                        {
                            "name": "name",
                            "path": "digitalHPS:lemma"
                        },
                        {
                            "name": "description",
                            "path": "digitalHPS:description"
                        },
                        {
                            "name": "concept_type",
                            "path": "digitalHPS:type[type_uri]"
                        },
                        {
                            "name": "identities",
                            "path": "digitalHPS:equal_to|,"
                        }
                    ]
                }
            },
            {
                "name": "search",
                "method": "GET",
                "path": "{endpoint}/ConceptLookup/{q}/noun",
                "parameters": [
                    {
                        "accept": "q",
                        "send": "q",
                        "required": true
                    }
                ],
                "response": {
                    "type": "xml",
                    "path": "digitalHPS:conceptEntry*",
                    "namespaces": [
                        {
                            "prefix": "digitalHPS",
                            "namespace": "http://www.digitalhps.org/"
                        }
                    ],
                    "parameters": [
                        {
                            "name": "name",
                            "path": "digitalHPS:lemma"
                        },
                        {
                            "name": "description",
                            "path": "digitalHPS:description"
                        },
                        {
                            "name": "concept_type",
                            "path": "digitalHPS:type[type_uri]"
                        },
                        {
                            "name": "identifier",
                            "path": "digitalHPS:id[concept_uri]"
                        },
                        {
                            "name": "identities",
                            "path": "digitalHPS:equal_to|,"
                        }
                    ]
                }
            }
        ]
    }
