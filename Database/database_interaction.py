#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3

def connect_to_db(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    return {'Connection':conn,'Cursor':c}

def insert_values_into(table_name: object, value_list: object, conn: object, c: object) -> object:
    values_bracket = '('+(','.join(['?']*len(value_list)))+')'
    sql_statement = "INSERT INTO "+table_name+" VALUES "+values_bracket
    c.execute(sql_statement, value_list)
    conn.commit()

def get_data(table_name, row_names, conn, before=None, after=None, min_max=False):
    '''Returns a list of Row objects. Data in each Row object can be accessed by integer or string indices'''
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if min_max == False:
        for elem in row_names:
            row_names[row_names.index(elem)] = elem+' as '+elem
    sql_statement = "SELECT "+','.join(row_names)+" FROM "+table_name
    if before:
        sql_statement = sql_statement + " WHERE date(creation_date)<date('" + before + "')"
        if after:
            sql_statement = sql_statement + " AND date(creation_date)>date('" + after + "')"
    else:
        if after:
            sql_statement = sql_statement + " WHERE date(creation_date)>date('" + after + "')"
        else:
            pass
    print(sql_statement)
    c.execute(sql_statement)
    return c



# conn_objects = connect_to_db('main_data.db')
# test_values = [15,'Tweet Text']
# insert_values_into('test_table',test_values,conn_objects['Connection'],conn_objects['Cursor'])