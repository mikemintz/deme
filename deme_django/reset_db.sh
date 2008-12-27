#!/bin/sh

rm -rf static/media/*
psql -U postgres -c "drop database deme_django;" ; psql -U postgres -c "create database deme_django WITH OWNER = postgres ENCODING = 'UTF8' TABLESPACE = pg_default;" && ./manage.py syncdb && ./create_initial_data.py test
