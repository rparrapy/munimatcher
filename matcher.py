#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# @author  Rodrigo Parra 
import dataset
from fuzzywuzzy import fuzz
from unidecode import unidecode
from unicodewriter import UnicodeWriter

DOUBT_THRESHOLD = 85
SUGGESTION_THRESHOLD = 49

# connecting to a PostgreSQL database
db = dataset.connect('postgresql://postgres:postgres@localhost:5432/playdb')

contratos = db.query("select distinct convocante from contrato where convocante like 'MUNICIPALIDAD%' order by convocante")
departamentos = [d['departamento'] for d in db.query("select distinct departamento from distrito order by departamento")]
fixes = {u'ÐEEMBUCU': u'ÑEEMBUCU'}

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
        departamento = fixes.get(departamento) if fixes.get(departamento) else departamento
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
        print u'%s) Ninguno de los anteriores. Seleccione el departamento de correspondiente de la siguiente lista:' % (len(options[municipio]) + 1)
        user_pick = input()
        if user_pick == len(options[municipio]) + 1:
            for i, d in enumerate(departamentos):
                print  u'%s) Departamento: %s' % (i + 1, d)
            user_pick = input()
            best_match[municipio] = (municipio, None, departamentos[user_pick - 1], None)
        else:
            best_match[municipio] = options[municipio][user_pick - 1]
    result.append((municipio, best_match[municipio][2]))

# for r in result:
#     print u'La Municipalidad de %s corresponde al departamento de %s' % r

with open('municipalidades.csv','w') as out:
    csv_out=UnicodeWriter(out)
    csv_out.writerow(['municipio','departamento'])
    for row in result:
        csv_out.writerow(row)

