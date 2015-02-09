#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# @author  Rodrigo Parra 
import dataset
from fuzzywuzzy import fuzz
from unidecode import unidecode

DOUBT_THRESHOLD = 85
SUGGESTION_THRESHOLD = 49

# connecting to a PostgreSQL database
db = dataset.connect('postgresql://postgres:postgres@localhost:5432/playdb')

contratos = db.query("select distinct convocante from contrato where convocante like 'MUNICIPALIDAD%' order by convocante")

best_match = {}
options = {}
result = []

for contrato in contratos:
    len_prefix = len('MUNICIPALIDAD DE ')
    municipio = contrato['convocante'].split('/')[0][len_prefix:].strip()
    highest_score = 0
    options[municipio] = []
    for d in db['distrito']:
        distrito = d['nombre'].strip()
        departamento = d['departamento'].strip()
        score = fuzz.ratio(unidecode(municipio), unidecode(distrito))
        value = (municipio, distrito, departamento, score)
        if score > highest_score:
            highest_score = score
            best_match[municipio] = value
        if score > SUGGESTION_THRESHOLD:
            options[municipio].append(value) 

under_threshold = [r for r in best_match.values() if r[-1] < DOUBT_THRESHOLD]
#print under_threshold
print "Existen %s Municipalidades en duda." % len(under_threshold)

for municipio in best_match.keys():
    if best_match[municipio][-1] < DOUBT_THRESHOLD:
        print u'¿A cual de los siguientes distritos corresponde la Municipalidad de %s?' % municipio
        options[municipio] = sorted(options[municipio], key=lambda option: option[-1], reverse=True)
        for i, opt in enumerate(options[municipio]):
            print u'%s) Distrito: %s Departamento: %s Similaridad: %s' % ((i + 1,) + opt[1:])
        user_pick = input()
        best_match[municipio] = options[municipio][user_pick - 1]
    result.append((municipio, best_match[municipio][2]))

for r in result:
    print u'La Municipalidad de %s corresponde al departamento de %s' % r


