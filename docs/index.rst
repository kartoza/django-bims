


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
 default_permissions : (u'add', u'change', u'delete')


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
   * - level
     - level
     - integer
     - 
     - 
     - 
     - Both
     -


Options::

 default_permissions : (u'add', u'change', u'delete')


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
   * - code name
     - code_name
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
   * - centroid
     - centroid
     - geometry(POINT,4326)
     - 
     - 
     - 
     - Both
     - 
   * - top level boundary
     - top_level_boundary
     - integer
     - 
     - 
     - True
     - Both
     - FK:bims.models.boundary.Boundary


Options::

 unique_together : (('name', 'code_name', 'type'),)
 default_permissions : (u'add', u'change', u'delete')


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
 default_permissions : (u'add', u'change', u'delete')


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
   * - Document for location context as JSON.
     - location_context_document
     - text
     - 
     - 
     - 
     - Both
     -


Options::

 default_permissions : (u'add', u'change', u'delete')


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

 default_permissions : (u'add', u'change', u'delete')


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
   * - Common Name
     - common_name
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - Scientific Name
     - scientific_name
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - Author
     - author
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - Kingdom
     - kingdom
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - Phylum
     - phylum
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - Class
     - taxon_class
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - Order
     - order
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - Family
     - family
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - Genus
     - genus
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - Species
     - species
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - Taxon ID
     - taxon_id
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - Accepted Name
     - accepted_name
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - Accepted Key
     - accepted_key
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - Vernacular Names
     - vernacular_names
     - varchar(100)[]
     - 
     - 
     - 
     - Both
     -


Options::

 default_permissions : (u'add', u'change', u'delete')


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
 default_permissions : (u'add', u'change', u'delete')


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

 default_permissions : (u'add', u'change', u'delete')


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
   * - collector or observer
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
     - FK:geonode.people.models.Profile
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

 default_permissions : (u'add', u'change', u'delete')
 permissions : (('can_upload_csv', 'Can upload CSV'), ('can_upload_shapefile', 'Can upload Shapefile'), ('can_validate_data', 'Can validate data'))


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
     - FK:geonode.people.models.Profile
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

 default_permissions : (u'add', u'change', u'delete')


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
 default_permissions : (u'add', u'change', u'delete')


category(bims.models.links.Category)
------------------------------------

::

 Category model for a link.

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
     - varchar(50)
     - 
     - True
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
   * - ordering
     - ordering
     - integer
     - 
     - 
     - 
     - 
     -


Options::

 ordering : ('ordering',)
 default_permissions : (u'add', u'change', u'delete')


link(bims.models.links.Link)
----------------------------

::

 Link model definition.

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
     - integer
     - 
     - 
     - True
     - 
     - FK:bims.models.links.Category
   * - name
     - name
     - varchar(50)
     - 
     - True
     - 
     - 
     - 
   * - url
     - url
     - varchar(200)
     - 
     - 
     - 
     - Both
     - 
   * - description
     - description
     - text
     - 
     - 
     - 
     - Blank
     - 
   * - ordering
     - ordering
     - integer
     - 
     - 
     - 
     - 
     -


Options::

 ordering : ('category__ordering', 'ordering')
 default_permissions : (u'add', u'change', u'delete')


Shapefile(bims.models.shapefile.Shapefile)
------------------------------------------

::

 Shapefile model
    

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
   * - shapefile
     - shapefile
     - varchar(100)
     - 
     - 
     - 
     - 
     - 
   * - token
     - token
     - varchar(100)
     - 
     - 
     - 
     - Both
     -


Options::

 default_permissions : (u'add', u'change', u'delete')


shapefileuploadsession-shapefile relationship(bims.models.shapefile_upload_session.ShapefileUploadSession_shapefiles)
---------------------------------------------------------------------------------------------------------------------

::

 ShapefileUploadSession_shapefiles(id, shapefileuploadsession, shapefile)

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
   * - shapefileuploadsession
     - shapefileuploadsession
     - integer
     - 
     - 
     - True
     - 
     - FK:bims.models.shapefile_upload_session.ShapefileUploadSession
   * - shapefile
     - shapefile
     - integer
     - 
     - 
     - True
     - 
     - FK:bims.models.shapefile.Shapefile


Options::

 unique_together : (('shapefileuploadsession', 'shapefile'),)
 default_permissions : (u'add', u'change', u'delete')


Shapefile Upload Session(bims.models.shapefile_upload_session.ShapefileUploadSession)
-------------------------------------------------------------------------------------

::

 Shapefile upload session model
    

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
   * - uploader
     - uploader
     - integer
     - 
     - 
     - True
     - Both
     - FK:geonode.people.models.Profile
   * - token
     - token
     - varchar(100)
     - 
     - 
     - 
     - Both
     - 
   * - uploaded at
     - uploaded_at
     - date
     - 
     - 
     - 
     - 
     - 
   * - processed
     - processed
     - boolean
     - 
     - 
     - 
     - Blank
     - 
   * - error
     - error
     - text
     - 
     - 
     - 
     - Both
     - 
   * - shapefiles
     - shapefiles
     - 
     - 
     - 
     - 
     - 
     - M2M:bims.models.shapefile.Shapefile (through: bims.models.shapefile_upload_session.ShapefileUploadSession_shapefiles)


Options::

 default_permissions : (u'add', u'change', u'delete')


non biodiversity layer(bims.models.non_biodiversity_layer.NonBiodiversityLayer)
-------------------------------------------------------------------------------

::

 Non biodiversity layer model.

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
     - True
     - 
     - 
     - 
   * - wms url
     - wms_url
     - varchar(256)
     - 
     - 
     - 
     - 
     - 
   * - wms layer name
     - wms_layer_name
     - varchar(128)
     - 
     - 
     - 
     - 
     - 
   * - wms format
     - wms_format
     - varchar(64)
     - 
     - 
     - 
     - 
     -


Options::

 default_permissions : (u'add', u'change', u'delete')


CSV Document(bims.models.csv_document.CSVDocument)
--------------------------------------------------

::

 Csv document model
    

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
   * - csv file
     - csv_file
     - varchar(100)
     - 
     - 
     - 
     - 
     -


Options::

 default_permissions : (u'add', u'change', u'delete')


Author(td_biblio.models.bibliography.Author)
--------------------------------------------

::

 Entry author

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
   * - First name
     - first_name
     - varchar(100)
     - 
     - 
     - 
     - 
     - 
   * - Last name
     - last_name
     - varchar(100)
     - 
     - 
     - 
     - 
     - 
   * - First Initial(s)
     - first_initial
     - varchar(10)
     - 
     - 
     - 
     - Blank
     - 
   * - user
     - user
     - integer
     - 
     - 
     - True
     - Both
     - FK:geonode.people.models.Profile


Options::

 ordering : ('last_name', 'first_name')
 default_permissions : (u'add', u'change', u'delete')


Editor(td_biblio.models.bibliography.Editor)
--------------------------------------------

::

 Journal or book editor

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
   * - First name
     - first_name
     - varchar(100)
     - 
     - 
     - 
     - 
     - 
   * - Last name
     - last_name
     - varchar(100)
     - 
     - 
     - 
     - 
     - 
   * - First Initial(s)
     - first_initial
     - varchar(10)
     - 
     - 
     - 
     - Blank
     - 
   * - user
     - user
     - integer
     - 
     - 
     - True
     - Both
     - FK:geonode.people.models.Profile


Options::

 ordering : ('last_name', 'first_name')
 default_permissions : (u'add', u'change', u'delete')


Journal(td_biblio.models.bibliography.Journal)
----------------------------------------------

::

 Peer reviewed journal

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
   * - Name
     - name
     - varchar(150)
     - 
     - 
     - 
     - 
     - 
   * - Entity abbreviation
     - abbreviation
     - varchar(100)
     - 
     - 
     - 
     - Blank
     -


Options::

 default_permissions : (u'add', u'change', u'delete')


Publisher(td_biblio.models.bibliography.Publisher)
--------------------------------------------------

::

 Journal or book publisher

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
   * - Name
     - name
     - varchar(150)
     - 
     - 
     - 
     - 
     - 
   * - Entity abbreviation
     - abbreviation
     - varchar(100)
     - 
     - 
     - 
     - Blank
     -


Options::

 default_permissions : (u'add', u'change', u'delete')


entry-editor relationship(td_biblio.models.bibliography.Entry_editors)
----------------------------------------------------------------------

::

 Entry_editors(id, entry, editor)

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
   * - entry
     - entry
     - integer
     - 
     - 
     - True
     - 
     - FK:td_biblio.models.bibliography.Entry
   * - editor
     - editor
     - integer
     - 
     - 
     - True
     - 
     - FK:td_biblio.models.bibliography.Editor


Options::

 unique_together : (('entry', u'editor'),)
 default_permissions : (u'add', u'change', u'delete')


from_entry-to_entry relationship(td_biblio.models.bibliography.Entry_crossref)
------------------------------------------------------------------------------

::

 Entry_crossref(id, from_entry, to_entry)

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
   * - from entry
     - from_entry
     - integer
     - 
     - 
     - True
     - 
     - FK:td_biblio.models.bibliography.Entry
   * - to entry
     - to_entry
     - integer
     - 
     - 
     - True
     - 
     - FK:td_biblio.models.bibliography.Entry


Options::

 unique_together : ((u'from_entry', u'to_entry'),)
 default_permissions : (u'add', u'change', u'delete')


Entry(td_biblio.models.bibliography.Entry)
------------------------------------------

::

 The core model for references

    Largely guided by the BibTeX file format (see
    http://en.wikipedia.org/wiki/BibTeX).

    Unsupported fields (for now):

    * eprint: A specification of an electronic publication, often a preprint
      or a technical report
    * howpublished: How it was published, if the publishing method is
      nonstandard
    * institution: The institution that was involved in the publishing, but not
      necessarily the publisher
    * key: A hidden field used for specifying or overriding the alphabetical
      order of entries (when the "author" and "editor" fields are missing).
      Note that this is very different from the key (mentioned just after this
      list) that is used to cite or cross-reference the entry.
    * series: The series of books the book was published in (e.g. "The Hardy
      Boys" or "Lecture Notes in Computer Science")
    * type: The field overriding the default type of publication (e.g.
      "Research Note" for techreport, "{PhD} dissertation" for phdthesis,
      "Section" for inbook/incollection)
    

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
   * - Entry type
     - type
     - varchar(50)
     - 
     - 
     - 
     - 
     - article:Article, book:Book, booklet:Book (no publisher), conference:Conference, inbook:Book chapter, incollection:Book from a collection, inproceedings:Conference proceedings article, manual:Technical documentation, mastersthesis:Master's Thesis, misc:Miscellaneous, phdthesis:PhD Thesis, proceedings:Conference proceedings, techreport:Technical report, unpublished:Unpublished work
   * - Title
     - title
     - varchar(255)
     - 
     - 
     - 
     - 
     - 
   * - journal
     - journal
     - integer
     - 
     - 
     - True
     - 
     - FK:td_biblio.models.bibliography.Journal
   * - Publication date
     - publication_date
     - date
     - 
     - 
     - 
     - Null
     - 
   * - Partial publication date?
     - is_partial_publication_date
     - boolean
     - 
     - 
     - 
     - Blank
     - 
   * - Volume
     - volume
     - varchar(50)
     - 
     - 
     - 
     - Blank
     - 
   * - Number
     - number
     - varchar(50)
     - 
     - 
     - 
     - Blank
     - 
   * - Pages
     - pages
     - varchar(50)
     - 
     - 
     - 
     - Blank
     - 
   * - URL
     - url
     - varchar(200)
     - 
     - 
     - 
     - Blank
     - 
   * - DOI
     - doi
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - ISSN
     - issn
     - varchar(20)
     - 
     - 
     - 
     - Blank
     - 
   * - ISBN
     - isbn
     - varchar(20)
     - 
     - 
     - 
     - Blank
     - 
   * - PMID
     - pmid
     - varchar(20)
     - 
     - 
     - 
     - Blank
     - 
   * - Book title
     - booktitle
     - varchar(50)
     - 
     - 
     - 
     - Blank
     - 
   * - Edition
     - edition
     - varchar(100)
     - 
     - 
     - 
     - Blank
     - 
   * - Chapter number
     - chapter
     - varchar(50)
     - 
     - 
     - 
     - Blank
     - 
   * - School
     - school
     - varchar(50)
     - 
     - 
     - 
     - Blank
     - 
   * - Organization
     - organization
     - varchar(50)
     - 
     - 
     - 
     - Blank
     - 
   * - publisher
     - publisher
     - integer
     - 
     - 
     - True
     - Both
     - FK:td_biblio.models.bibliography.Publisher
   * - Address
     - address
     - varchar(250)
     - 
     - 
     - 
     - Blank
     - 
   * - Annote
     - annote
     - varchar(250)
     - 
     - 
     - 
     - Blank
     - 
   * - Note
     - note
     - text
     - 
     - 
     - 
     - Blank
     - 
   * - authors
     - authors
     - 
     - 
     - 
     - 
     - 
     - M2M:td_biblio.models.bibliography.Author (through: td_biblio.models.bibliography.AuthorEntryRank)
   * - editors
     - editors
     - 
     - 
     - 
     - 
     - Blank
     - M2M:td_biblio.models.bibliography.Editor (through: td_biblio.models.bibliography.Entry_editors)
   * - crossref
     - crossref
     - 
     - 
     - 
     - 
     - Blank
     - M2M:td_biblio.models.bibliography.Entry (through: td_biblio.models.bibliography.Entry_crossref)


Options::

 ordering : ('-publication_date',)
 default_permissions : (u'add', u'change', u'delete')


collection-entry relationship(td_biblio.models.bibliography.Collection_entries)
-------------------------------------------------------------------------------

::

 Collection_entries(id, collection, entry)

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
   * - collection
     - collection
     - integer
     - 
     - 
     - True
     - 
     - FK:td_biblio.models.bibliography.Collection
   * - entry
     - entry
     - integer
     - 
     - 
     - True
     - 
     - FK:td_biblio.models.bibliography.Entry


Options::

 unique_together : (('collection', u'entry'),)
 default_permissions : (u'add', u'change', u'delete')


Collection(td_biblio.models.bibliography.Collection)
----------------------------------------------------

::

 Define a collection of entries

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
   * - Name
     - name
     - varchar(100)
     - 
     - 
     - 
     - 
     - 
   * - Short description
     - short_description
     - text
     - 
     - 
     - 
     - Both
     - 
   * - entries
     - entries
     - 
     - 
     - 
     - 
     - 
     - M2M:td_biblio.models.bibliography.Entry (through: td_biblio.models.bibliography.Collection_entries)


Options::

 default_permissions : (u'add', u'change', u'delete')


Author Entry Rank(td_biblio.models.bibliography.AuthorEntryRank)
----------------------------------------------------------------

::

 Give the author rank for an entry author sequence

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
   * - author
     - author
     - integer
     - 
     - 
     - True
     - 
     - FK:td_biblio.models.bibliography.Author
   * - entry
     - entry
     - integer
     - 
     - 
     - True
     - 
     - FK:td_biblio.models.bibliography.Entry
   * - Rank
     - rank
     - integer
     - 
     - 
     - 
     - 
     -


Options::

 ordering : ('rank',)
 default_permissions : (u'add', u'change', u'delete')



