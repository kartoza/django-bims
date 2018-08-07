


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



