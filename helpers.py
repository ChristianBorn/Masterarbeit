#!/usr/bin/python
# -*- coding: utf-8 -*-
def elem_count(liste):
	#Zählt alle Elemente der Liste, gibt ein Dictionary aus
	counted = {}
	for elem in liste:
		if elem not in counted:
			counted[elem] = 1
		else:
			counted[elem] = counted[elem] + 1
	return counted

def sort_dict(dictionary, rev=True):
	#Sortiert Dictionary, gibt Schlüssel-Wert Paare als Tupel aus
	sorted_dict = sorted(
        dictionary.items(),
        key=lambda k_v: k_v[1],
        reverse=True)
	return sorted_dict

def max_key(dictionary):
	return max(dictionary, key=dictionary.get)