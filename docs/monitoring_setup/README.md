Prometheus Grafana setup
========================

Firstly you need add this projects URL to the prometheus.yml file for the installed prometheus on the system

For example for the local setup:

 ```
    - job_name: Django-bims
    # If django_prometheus metric exporter is installed and configured,
    # it will export bims metrics.
    static_configs:
      - targets: ['0.0.0.0:63302']
    scrape_interval: 5s
    scrape_timeout: 15s
```


Then to set up the dashboard in grafana remove the .TEMPLATE extension in the example dashbord file in the docs and setup a data source to point to the prometheus running instance URL such as *http://localhost:9090*, and then import the template dashboard*
