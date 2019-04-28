# -*- encoding:utf-8 -*-
from sqlalchemy import *

class OrmTable(object):
    def __init__(self, engine, tablename):
        self.engine = engine
        self.table = Table(tablename, MetaData(engine), autoload=True)

    def insert(self, **kwargs):
        stmt = self.table.insert().values(
            kwargs
        )
        self.engine.connect().execute(stmt)

    def _generateAndStr(self, keydict):
        andList = []
        for k, v in keydict.items():
            if isinstance(v, tuple) and len(v) == 2:
                if v[0] == "!=":
                    andList.append("self.table.c.%s != '%s'" % (k, str(v[1])))
                elif v[0] == "like":
                    andList.append("self.table.c.%s.like('%s')" % (k, v[1]))
                elif v[0] == "not like":
                    andList.append("~self.table.c.%s.like('%s')" % (k, v[1]))
                elif v[0] == "in":
                    andList.append("self.table.c.%s.in_(%s)" % (k, str(v[1])))
                elif v[0] == "not in":
                    andList.append("~self.table.c.%s.in_(%s)" % (k, str(v[1])))
                else:
                    raise Exception("unsupport operation:%s" % v[0])
            else:
                andList.append("self.table.c.%s == '%s'" % (k, v))

        return ','.join(andList)

    def delete(self, **kwargs):
        andStr = self._generateAndStr(kwargs)
        evalStr = "self.table.delete().where(and_(%s))" % andStr
        stmt = eval(evalStr)
        self.engine.connect().execute(stmt)

    def select(self, **kwargs):
        andStr = self._generateAndStr(kwargs)
        evalStr = "select([self.table]).where(and_(%s))" % andStr
        stmt = eval(evalStr)
        result = self.engine.connect().execute(stmt)
        return result

    def update(self, where={}, **kwargs):
        andStr = self._generateAndStr(where)
        evalStr = "self.table.update().values(kwargs).where(and_(%s))" % andStr
        stmt = eval(evalStr)
        self.engine.connect().execute(stmt)

    @property
    def count(self):
        stmt = select([self.table])
        result = self.engine.connect().execute(stmt).fetchall()
        count = len(result) if result else 0
        return count

    def maxRowValue(self, rowname):
        evalStr = "select([func.max(self.table.c.%s)])" % rowname
        stmt = eval(evalStr)
        result = self.engine.connect().execute(stmt).fetchone()
        return result[0]

