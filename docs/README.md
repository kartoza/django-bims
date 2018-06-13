LEDET-BIMS documentation
==============================

## Technical documentation for LEDET-BIMS Project.

## Firstly you need to be in the base project directory where the management
 command is run from.

```docs/docs/```

**Then to generated the documentation run **
```python manage.py listing_models --output docs/docs/index.rst
```

Options
--app(-a)
You can pass specific app name. Listing only the specified app.

``` python manage.py listing_models --app fish
```
--output(-o)
It writes the results to the specified file.

```python manage.py listing_models --output index.rst
```
--format(-f)
You can choice output format. rst (reStructuredText) or md (Markdown). Default format is rst.

```python manage.py listing_models --format md
```




