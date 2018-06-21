


.. contents::
   :local:


location type(bims.models.location_type.LocationType)
-----------------------------------------------------

::

 Location type model.

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - PK
     - Unique
     - Index
     - Null/Blank
     - Comment
   * - ID
     - id
     - serial
     - True
     - True
     - 
     - Blank
     - 
   * - name
     - name
     - varchar(100)
     - 
     - 
     - 
     - 
     - 
   * - description
     - description
     - text
     - 
     - 
     - 
     - Both
     - 
   * - allowed geometry
     - allowed_geometry
     - varchar(20)
     - 
     - 
     - 
     - 
     - POINT:Point, LINE:Line, POLYGON:Polygon, MULTIPOLYGON:Multipolygon


Options::

 ordering : ['name']
 default_permissions : ('add', 'change', 'delete')


location context(bims.models.location_context.LocationContext)
--------------------------------------------------------------

::

 LocationContext(id, context_document)

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - PK
     - Unique
     - Index
     - Null/Blank
     - Comment
   * - ID
     - id
     - serial
     - True
     - True
     - 
     - Blank
     - 
   * - context document
     - context_document
     - text
     - 
     - 
     - 
     - 
     -


Options::

 default_permissions : ('add', 'change', 'delete')


boundary type(bims.models.boundary_type.BoundaryType)
-----------------------------------------------------

::

 Boundary type model.

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - PK
     - Unique
     - Index
     - Null/Blank
     - Comment
   * - ID
     - id
     - serial
     - True
     - True
     - 
     - Blank
     - 
   * - name
     - name
     - varchar(128)
     - 
     - True
     - 
     - 
     -


Options::

 default_permissions : ('add', 'change', 'delete')


boundary(bims.models.boundary.Boundary)
---------------------------------------

::

 Boundary model.

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - PK
     - Unique
     - Index
     - Null/Blank
     - Comment
   * - ID
     - id
     - serial
     - True
     - True
     - 
     - Blank
     - 
   * - name
     - name
     - varchar(128)
     - 
     - 
     - 
     - 
     - 
   * - type
     - type
     - integer
     - 
     - 
     - True
     - 
     - FK:bims.models.boundary_type.BoundaryType
   * - geometry
     - geometry
     - geometry(MULTIPOLYGON,4326)
     - 
     - 
     - 
     - Both
     -


Options::

 unique_together : (('name', 'type'),)
 default_permissions : ('add', 'change', 'delete')


cluster(bims.models.cluster.Cluster)
------------------------------------

::

 Cluster model.

    The cluster model creates pre-computer spatial cluster analysis for all
    sites and all record in a geographic region.
    The clustering is based on :
    - different geographical areas for different scales.
    - module of record based on biological_collection model. E.g. Fish.

    E.g. small scales will cluster by country, larger scale by province,
    catchment etc.
    The cluster units are configurable based on the boundary model.
    

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - PK
     - Unique
     - Index
     - Null/Blank
     - Comment
   * - ID
     - id
     - serial
     - True
     - True
     - 
     - Blank
     - 
   * - boundary
     - boundary
     - integer
     - 
     - 
     - True
     - 
     - FK:bims.models.boundary.Boundary
   * - module
     - module
     - varchar(128)
     - 
     - 
     - 
     - 
     - 
   * - site count
     - site_count
     - integer
     - 
     - 
     - 
     - 
     - 
   * - details
     - details
     - text
     - 
     - 
     - 
     - 
     -


Options::

 unique_together : (('boundary', 'module'),)
 default_permissions : ('add', 'change', 'delete')


location site(bims.models.location_site.LocationSite)
-----------------------------------------------------

::

 Location Site model.

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - PK
     - Unique
     - Index
     - Null/Blank
     - Comment
   * - ID
     - id
     - serial
     - True
     - True
     - 
     - Blank
     - 
   * - name
     - name
     - varchar(100)
     - 
     - 
     - 
     - 
     - 
   * - location type
     - location_type
     - integer
     - 
     - 
     - True
     - 
     - FK:bims.models.location_type.LocationType
   * - geometry point
     - geometry_point
     - geometry(POINT,4326)
     - 
     - 
     - 
     - Both
     - 
   * - geometry line
     - geometry_line
     - geometry(LINESTRING,4326)
     - 
     - 
     - 
     - Both
     - 
   * - geometry polygon
     - geometry_polygon
     - geometry(POLYGON,4326)
     - 
     - 
     - 
     - Both
     - 
   * - geometry multipolygon
     - geometry_multipolygon
     - geometry(MULTIPOLYGON,4326)
     - 
     - 
     - 
     - Both
     - 
   * - location context
     - location_context
     - integer
     - 
     - 
     - True
     - Both
     - FK:bims.models.location_context.LocationContext


Options::

 default_permissions : ('add', 'change', 'delete')


IUCN Status(bims.models.iucn_status.IUCNStatus)
-----------------------------------------------

::

 IUCN status model.

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - PK
     - Unique
     - Index
     - Null/Blank
     - Comment
   * - ID
     - id
     - serial
     - True
     - True
     - 
     - Blank
     - 
   * - category
     - category
     - varchar(50)
     - 
     - 
     - 
     - Blank
     - LC:Least Concern, NT:Near Threatened, VU:Vulnerable, EN:Endangered, CR:Critically Endangered, EW:Extinct In The Wild, EX:Extinct
   * - sensitive
     - sensitive
     - boolean
     - 
     - 
     - 
     - Blank
     -


Options::

 default_permissions : ('add', 'change', 'delete')


Taxon(bims.models.taxon.Taxon)
------------------------------

::

 Taxon model.

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - PK
     - Unique
     - Index
     - Null/Blank
     - Comment
   * - ID
     - id
     - serial
     - True
     - True
     - 
     - Blank
     - 
   * - GBIF id
     - gbif_id
     - integer
     - 
     - 
     - 
     - Both
     - 
   * - iucn status
     - iucn_status
     - integer
     - 
     - 
     - True
     - Both
     - FK:bims.models.iucn_status.IUCNStatus
   * - common name
     - common_name
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - scientific name
     - scientific_name
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - author
     - author
     - varchar(100)
     - 
     - 
     - 
     - Blank
     -


Options::

 default_permissions : ('add', 'change', 'delete')


survey-locationsite relationship(bims.models.survey.Survey_sites)
-----------------------------------------------------------------

::

 Survey_sites(id, survey, locationsite)

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - PK
     - Unique
     - Index
     - Null/Blank
     - Comment
   * - ID
     - id
     - serial
     - True
     - True
     - 
     - Blank
     - 
   * - survey
     - survey
     - integer
     - 
     - 
     - True
     - 
     - FK:bims.models.survey.Survey
   * - locationsite
     - locationsite
     - integer
     - 
     - 
     - True
     - 
     - FK:bims.models.location_site.LocationSite


Options::

 unique_together : (('survey', 'locationsite'),)
 default_permissions : ('add', 'change', 'delete')


survey(bims.models.survey.Survey)
---------------------------------

::

 Survey model.

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - PK
     - Unique
     - Index
     - Null/Blank
     - Comment
   * - ID
     - id
     - serial
     - True
     - True
     - 
     - Blank
     - 
   * - date
     - date
     - date
     - 
     - 
     - 
     - 
     - 
   * - sites
     - sites
     - 
     - 
     - 
     - 
     - 
     - M2M:bims.models.location_site.LocationSite (through: bims.models.survey.Survey_sites)


Options::

 default_permissions : ('add', 'change', 'delete')


biological collection record(bims.models.biological_collection_record.BiologicalCollectionRecord)
-------------------------------------------------------------------------------------------------

::

 Biological collection model.

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - PK
     - Unique
     - Index
     - Null/Blank
     - Comment
   * - ID
     - id
     - serial
     - True
     - True
     - 
     - Blank
     - 
   * - site
     - site
     - integer
     - 
     - 
     - True
     - 
     - FK:bims.models.location_site.LocationSite
   * - original species name
     - original_species_name
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - category
     - category
     - varchar(50)
     - 
     - 
     - 
     - Blank
     - alien:Alien, indigenous:Indigenous, translocated:Translocated
   * - present
     - present
     - boolean
     - 
     - 
     - 
     - Blank
     - 
   * - absent
     - absent
     - boolean
     - 
     - 
     - 
     - Blank
     - 
   * - collection date
     - collection_date
     - date
     - 
     - 
     - 
     - 
     - 
   * - collector
     - collector
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - owner
     - owner
     - integer
     - 
     - 
     - True
     - Both
     - FK:django.contrib.auth.models.User
   * - notes
     - notes
     - text
     - 
     - 
     - 
     - Blank
     - 
   * - Taxon GBIF 
     - taxon_gbif_id
     - integer
     - 
     - 
     - True
     - Both
     - FK:bims.models.taxon.Taxon
   * - validated
     - validated
     - boolean
     - 
     - 
     - 
     - Blank
     -


Options::

 default_permissions : ('add', 'change', 'delete')


profile(bims.models.profile.Profile)
------------------------------------

::

 Profile(id, user, qualifications, other)

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - PK
     - Unique
     - Index
     - Null/Blank
     - Comment
   * - ID
     - id
     - serial
     - True
     - True
     - 
     - Blank
     - 
   * - user
     - user
     - integer
     - 
     - True
     - True
     - 
     - FK:django.contrib.auth.models.User
   * - qualifications
     - qualifications
     - varchar(250)
     - 
     - 
     - 
     - Blank
     - 
   * - other
     - other
     - varchar(100)
     - 
     - 
     - 
     - Blank
     -


Options::

 default_permissions : ('add', 'change', 'delete')


carousel header(bims.models.carousel_header.CarouselHeader)
-----------------------------------------------------------

::

 Carousel header model.

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - PK
     - Unique
     - Index
     - Null/Blank
     - Comment
   * - ID
     - id
     - serial
     - True
     - True
     - 
     - Blank
     - 
   * - order
     - order
     - integer
     - 
     - 
     - True
     - 
     - 
   * - banner
     - banner
     - varchar(100)
     - 
     - 
     - 
     - 
     - 
   * - description
     - description
     - text
     - 
     - 
     - 
     - Blank
     -


Options::

 ordering : ('order',)
 default_permissions : ('add', 'change', 'delete')



