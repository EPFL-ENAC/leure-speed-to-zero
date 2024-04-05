#!/usr/bin/env bash


find /webservice/eucalc/dev/_interactions/data/database_dump -name '*.sql' | awk '{ print "source",$0 }' | mysql --batch -u root -p levers