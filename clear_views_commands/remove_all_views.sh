#!/bin/sh

echo 'DROP ALL VIEWS'
psql -d gis -f drop_views.txt -o commands.txt

python clear_first_and_second_line.py

psql -d gis -f commands.txt

echo 'DROP ALL MATERIALIZED VIEWS'
psql -d gis -f drop_materialized_views.txt -o commands.txt

python clear_first_and_second_line.py

psql -d gis -f commands.txt