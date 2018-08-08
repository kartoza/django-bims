from kombu import Exchange, Queue

geoserver_exchange = Exchange("geonode", type="topic", durable=False)

queue_all_events = Queue("broadcast", geoserver_exchange, routing_key="#")
queue_email_events = Queue("email.events", geoserver_exchange, routing_key="email")
queue_geoserver = Queue("all.geoserver", geoserver_exchange, routing_key="geoserver.#")
queue_geoserver_catalog = Queue("geoserver.catalog", geoserver_exchange, routing_key="geoserver.catalog")
queue_geoserver_data = Queue("geoserver.data", geoserver_exchange, routing_key="geoserver.catalog")
queue_geoserver_events = Queue("geoserver.events", geoserver_exchange, routing_key="geonode.geoserver")
queue_notifications_events = Queue("notifications.events", geoserver_exchange, routing_key="notifications")
queue_layer_viewers = Queue("geonode.layer.viewer", geoserver_exchange, routing_key="geonode.viewer")

GEONODE_QUEUES = (queue_all_events,
          queue_email_events,
          queue_geoserver,
          queue_geoserver_catalog,
          queue_geoserver_data,
          queue_geoserver_events,
          queue_notifications_events,
          queue_layer_viewers)
