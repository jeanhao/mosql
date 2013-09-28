#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import deque

class Database(object):
    '''It is a context manager which manages the creation and destruction of a
    connection and its cursors.

    :param module: a module which conforms Python DB API 2.0

    Initialize a :class:`Database` instance:

    ::

        import psycopg2
        db = Database(psycopg2, host='127.0.0.1')

    Note it just tells :class:`Database` how to connect to your database. No
    connection or cursor is created here.

    Then get a cursor to communicate with database:

    ::

        with db as cur:
            cur.execute('select 1')

    The connection and cursor are created when you enter the with-block, and
    they will be closed when you leave. Also, the changes will be committed when
    you leave, or be rollbacked if there is any exception.

    If you need multiple cursors, just say:

    ::

        with db as cur1, db as cur2:
            cur1.execute('select 1')
            cur2.execute('select 2')

    Each :class:`Database` instance at most has one connection. The cursors
    share a same connection no matter how many cursors you asked.

    It is possible to customize the creating of connection or cursor. If you
    want to customize, override the attributes you need:

    ::

        db = Database()
        db.getconn = lambda: pool.getconn()
        db.putconn = lambda conn: pool.putconn(conn)
        db.getcur  = lambda conn: conn.cursor('named-cusor')

    You can set them ``None`` to back the default way.
    '''

    def __init__(self, module=None, *conn_args, **conn_kargs):

        if module is not None:
            self._getconn = lambda: module.connect(*conn_args, **conn_kargs)
        else:
            self._getconn = None

        # set them None to use the default way
        self.getconn = None
        self.putconn = None
        self.getcur = None

        self._conn = None
        self._cur_stack = deque()

    def __enter__(self):

        # check if we need to create connection
        if not self._cur_stack:
            if self.getconn:
                self._conn = self.getconn()
            else:
                assert self._getconn, "You must set getconn if you don't specifiy a module."
                self._conn = self._getconn()

        # get the cursor
        if self.getcur:
            cur = self.getcur(self._conn)
        else:
            cur = self._conn.cursor()

        # push it into stack
        self._cur_stack.append(cur)

        return cur

    def __exit__(self, exc_type, exc_val, exc_tb):

        # close the cursor
        cur = self._cur_stack.pop()
        cur.close()

        # rollback or commit
        if exc_type:
            self._conn.rollback()
        else:
            self._conn.commit()

        # close the connection if all cursors are closed
        if not self._cur_stack:

            if self.putconn:
                self.putconn(self._conn)
            else:
                self._conn.close()

def extact_col_names(cur):
    '''Extacts the column names from a cursor.

    :rtype: list
    '''
    return [desc.name for desc in cur.description]

def one_to_dict(cur):
    '''Fetch one row from a cursor and make it as a dict.

    :rtype: dict
    '''
    return dict(zip(extact_col_names(cur), cur.fetchone()))

def all_to_dicts(cur):
    '''Fetch all rows from a cursor and make it as dicts in a list.

    :rtype: dicts in list
    '''
    return [dict(zip(extact_col_names(cur), row)) for row in cur]




if __name__ == '__main__':
    import doctest
    doctest.testmod()
