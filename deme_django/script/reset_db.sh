#!/bin/sh

cur_dir=`dirname $0`
base_dir="$cur_dir/.."
rm -rf "$base_dir/static/filedocument/*"
psql -U postgres -c "drop database deme_django;"
psql -U postgres -c "create database deme_django WITH OWNER = postgres ENCODING = 'UTF8' TABLESPACE = pg_default;"
$base_dir/manage.py syncdb --all
$base_dir/manage.py migrate --fake
$base_dir/script/create_initial_data.py test
#$base_dir/script/create_initial_data.py 
