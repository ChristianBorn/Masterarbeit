#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3

def connect_to_db(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    return {'Connection':conn,'Cursor':c}

def insert_values_into(table_name, value_list, conn, c):
    values_bracket = '('+(','.join(['?']*len(value_list)))+')'
    sql_statement = "INSERT INTO "+table_name+" VALUES "+values_bracket
    print(sql_statement)
    print(value_list)
    c.execute(sql_statement, value_list)
    conn.commit()

# conn_objects = connect_to_db('main_data.db')
# test_values = [15,'Tweet Text']
# insert_values_into('test_table',test_values,conn_objects['Connection'],conn_objects['Cursor'])