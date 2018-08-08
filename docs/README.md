LEDET-BIMS documentation
==============================

Technical documentation for the Project.

Firstly you need to be in django-bims folder and then access the management command in the docker container
 with.

 ```make shell```


Then to generated the documentation run

```python manage.py listing_models --output docs/index.rst```

Options
--app(-a)
You can pass specific app name. Listing only the specified app.

```python manage.py listing_models --app fish```

--output(-o)
It writes the results to the specified file.

```python manage.py listing_models --output index.rst```

--format(-f)
You can choose the output format. rst (reStructuredText) or md (Markdown). Default format is rst.

```python manage.py listing_models --format md```




