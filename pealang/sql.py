
"""PeaLang 0.44 SQL and database adapter foundation."""
from __future__ import annotations
from dataclasses import dataclass
from contextlib import contextmanager
import sqlite3
from .data import DataFrame

@dataclass(frozen=True)
class DatabaseSpec:
    scheme:str
    driver:str
    paramstyle:str='qmark'
    optional_dependency:str|None=None

DATABASES={
 'sqlite':DatabaseSpec('sqlite','sqlite3'),
 'duckdb':DatabaseSpec('duckdb','duckdb','qmark','duckdb'),
 'postgresql':DatabaseSpec('postgresql','psycopg','pyformat','psycopg[binary]'),
 'postgres':DatabaseSpec('postgres','psycopg','pyformat','psycopg[binary]'),
 'mysql':DatabaseSpec('mysql','pymysql','pyformat','pymysql'),
 'mariadb':DatabaseSpec('mariadb','pymysql','pyformat','pymysql'),
 'sqlserver':DatabaseSpec('sqlserver','pyodbc','qmark','pyodbc'),
 'mssql':DatabaseSpec('mssql','pyodbc','qmark','pyodbc'),
 'oracle':DatabaseSpec('oracle','oracledb','named','oracledb'),
}

def _scheme(uri):return str(uri).split('://',1)[0].lower() if '://' in str(uri) else 'sqlite'
def _sqlite_path(uri):
    value=str(uri)
    if value.startswith('sqlite:///'):return value[10:]
    if value.startswith('sqlite://'):return value[9:]
    return value

def connect(uri,**options):
    scheme=_scheme(uri);spec=DATABASES.get(scheme)
    if not spec:raise ValueError('Unsupported database scheme: '+scheme)
    if scheme=='sqlite':
        conn=sqlite3.connect(_sqlite_path(uri),timeout=float(options.get('timeout',5)));conn.row_factory=sqlite3.Row;return Database(conn,spec,str(uri))
    try:module=__import__(spec.driver)
    except ImportError as exc:raise RuntimeError(f"{scheme} adapter requires optional dependency: {spec.optional_dependency}") from exc
    dsn=options.pop('dsn',str(uri).split('://',1)[1])
    if scheme=='duckdb':conn=module.connect(dsn)
    elif scheme in ('postgresql','postgres'):conn=module.connect(dsn,**options)
    elif scheme in ('mysql','mariadb'):
        from urllib.parse import urlparse
        u=urlparse(str(uri));conn=module.connect(host=u.hostname,user=u.username,password=u.password,database=u.path.lstrip('/'),port=u.port or 3306,**options)
    elif scheme in ('sqlserver','mssql'):conn=module.connect(dsn,**options)
    elif scheme=='oracle':conn=module.connect(dsn=dsn,**options)
    else:raise ValueError('Unsupported database scheme: '+scheme)
    return Database(conn,spec,str(uri))

class Database:
    def __init__(self,connection,spec,uri=''):self.connection,self.spec,self.uri=connection,spec,uri
    def close(self):return self.connection.close()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def execute(self,sql,params=None):
        cur=self.connection.cursor();cur.execute(sql,params or ());return cur
    def query(self,sql,params=None):
        cur=self.execute(sql,params);cols=[x[0] for x in (cur.description or [])];return DataFrame([dict(zip(cols,row)) for row in cur.fetchall()])
    def scalar(self,sql,params=None):
        row=self.execute(sql,params).fetchone();return None if row is None else row[0]
    def executemany(self,sql,rows):
        cur=self.connection.cursor();cur.executemany(sql,list(rows));return cur
    def commit(self):self.connection.commit();return self
    def rollback(self):self.connection.rollback();return self
    @contextmanager
    def transaction(self):
        try:yield self;self.connection.commit()
        except Exception:self.connection.rollback();raise
    def tables(self):
        s=self.spec.scheme
        if s=='sqlite':return [r['name'] for r in self.query("select name from sqlite_master where type='table' order by name").to_dicts()]
        if s=='duckdb':return [r['table_name'] for r in self.query("select table_name from information_schema.tables where table_schema='main' order by table_name").to_dicts()]
        return [next(iter(r.values())) for r in self.query('select table_name from information_schema.tables').to_dicts()]
    def columns(self,table):
        if self.spec.scheme=='sqlite':return self.query('pragma table_info("'+str(table).replace('"','""')+'")').to_dicts()
        return self.query('select column_name,data_type,is_nullable from information_schema.columns where table_name = ?', [table]).to_dicts()
    def insert_frame(self,table,frame,batch_size=1000):
        rows=frame.to_dicts()
        if not rows:return 0
        cols=frame.columns;quoted=','.join('"'+c.replace('"','""')+'"' for c in cols);marks=','.join('?' for _ in cols)
        sql=f'insert into "{table.replace(chr(34),chr(34)*2)}" ({quoted}) values ({marks})'
        total=0
        for i in range(0,len(rows),int(batch_size)):
            vals=[[r.get(c) for c in cols] for r in rows[i:i+int(batch_size)]];self.executemany(sql,vals);total+=len(vals)
        return total
    def upsert_frame(self,table,frame,key_columns,batch_size=1000):
        if self.spec.scheme!='sqlite':raise NotImplementedError('Portable upsert is implemented for SQLite in 0.44; other adapters expose transactions/batching pending dialect-specific merge SQL')
        rows=frame.to_dicts()
        if not rows:return 0
        cols=frame.columns;keys=[key_columns] if isinstance(key_columns,str) else list(key_columns);updates=[c for c in cols if c not in keys]
        q=lambda x:'"'+x.replace('"','""')+'"';sql=f'insert into {q(table)} ({",".join(map(q,cols))}) values ({",".join("?" for _ in cols)}) on conflict ({",".join(map(q,keys))}) do update set '+','.join(f'{q(c)}=excluded.{q(c)}' for c in updates)
        return self.insert_sql_many(sql,[[r.get(c) for c in cols] for r in rows],batch_size)
    def insert_sql_many(self,sql,rows,batch_size=1000):
        rows=list(rows);total=0
        for i in range(0,len(rows),int(batch_size)):batch=rows[i:i+int(batch_size)];self.executemany(sql,batch);total+=len(batch)
        return total

def read_sql(uri,sql,params=None,**options):
    with connect(uri,**options) as db:return db.query(sql,params)
def execute_sql(uri,sql,params=None,**options):
    with connect(uri,**options) as db:
        with db.transaction():cur=db.execute(sql,params);return cur.rowcount

