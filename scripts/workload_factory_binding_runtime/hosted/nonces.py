"""Explicit private one-attempt state; retained consumption precedes provider I/O."""
from contextlib import closing, contextmanager
import os
from pathlib import Path
import re
import sqlite3
import stat
import time
from workload_factory_binding.evidence import BindingError, integer, require, valid_digest
from ..config import _handle
ERROR = "hosted-issuance-refused"
DATABASE = "issuance.sqlite"
class Unavailable(BindingError):
    """Safe internal outage marker; never treat as authenticated peer denial."""
    pass
SCHEMA = (
    "CREATE TABLE metadata (version INTEGER NOT NULL, highwater INTEGER NOT NULL)",
    "CREATE TABLE attempts (ref TEXT PRIMARY KEY, nonce TEXT UNIQUE NOT NULL, commitment TEXT NOT NULL, state TEXT NOT NULL, token_digest TEXT)",
)


def identity(directory):
    p=Path(directory).absolute()
    require(p.resolve()==p,ERROR)
    a,b=p.lstat(),(p/DATABASE).lstat()
    require(stat.S_ISDIR(a.st_mode) and stat.S_ISREG(b.st_mode) and b.st_nlink==1
            and all(x.st_uid==os.geteuid() and not x.st_mode&0o077 for x in (a,b)),ERROR)
    for suffix in ("-journal","-wal","-shm"):
        x=p/(DATABASE+suffix)
        if x.exists() or x.is_symlink():
            s=x.lstat();require(suffix=="-journal" and stat.S_ISREG(s.st_mode)
                and s.st_nlink==1 and s.st_uid==os.geteuid() and not s.st_mode&0o077,ERROR)
    return a.st_dev,a.st_ino,b.st_dev,b.st_ino


class NonceLedger:
    @classmethod
    def initialize(cls,directory):
        try:
            p=Path(directory).absolute();p.mkdir(mode=0o700)
            fd=os.open(p/DATABASE,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
            with closing(sqlite3.connect(p/DATABASE)) as db,db:
                db.execute("PRAGMA synchronous=FULL")
                for sql in SCHEMA:db.execute(sql)
                db.execute("INSERT INTO metadata VALUES (1,0)")
            fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(fd)
            finally:os.close(fd)
            return identity(p)
        except Exception:raise BindingError(ERROR) from None

    def __init__(self,directory,*,identity):
        self.directory=Path(directory).absolute();self.identity=identity
        try:require(globals()["identity"](self.directory)==identity,ERROR)
        except Exception:raise BindingError(ERROR) from None

    @contextmanager
    def transaction(self,decision):
        db=None
        try:
            decision.now();require(identity(self.directory)==self.identity,ERROR)
            db=sqlite3.connect((self.directory/DATABASE).as_uri()+"?mode=rw",uri=True,
                timeout=min(2,decision.remaining()),isolation_level=None)
            end=time.monotonic()+min(2,decision.remaining());db.set_progress_handler(lambda:int(time.monotonic()>=end),100)
            db.execute("PRAGMA synchronous=FULL")
            require(db.execute("PRAGMA journal_mode").fetchone()==("delete",),ERROR)
            actual=tuple(x[0] for x in db.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name"))
            require(actual==tuple(sorted(SCHEMA,key=lambda x:x.split()[2])),ERROR)
            db.execute("BEGIN IMMEDIATE")
            meta=db.execute("SELECT version,highwater FROM metadata").fetchall();now=decision.now()
            require(len(meta)==1 and meta[0][0]==1 and integer(meta[0][1]) and now>=meta[0][1],ERROR)
            db.execute("UPDATE metadata SET highwater=?",(now,));db.execute("SAVEPOINT business")
            failed=True
            try:
                yield db
                decision.now();require(identity(self.directory)==self.identity,ERROR);failed=False
            finally:
                if failed:db.execute("ROLLBACK TO business")
                db.execute("RELEASE business");db.execute("COMMIT")
        except Exception as error:
            if db is not None and db.in_transaction:db.execute("ROLLBACK")
            if isinstance(error,(OSError,sqlite3.OperationalError)):raise Unavailable(ERROR) from None
            raise BindingError(ERROR) from None
        finally:
            if db is not None:db.close()

    def reserve(self,ref,nonce,commitment,*,decision):
        _handle(ref);require(type(nonce) is str and re.fullmatch(r"[0-9a-f]{64}",nonce)
                             and valid_digest(commitment),ERROR)
        with self.transaction(decision) as db:
            db.execute("INSERT INTO attempts VALUES (?,?,?,'consumed',NULL)",(ref,nonce,commitment))

    def transition(self,ref,old,new,*,decision,token_digest=None):
        _handle(ref);require(type(old) is tuple and old and set(old)<={"consumed","issued","retiring"}
            and new in ("consumed","issued","retiring","retired")
            and (token_digest is None or valid_digest(token_digest)),ERROR)
        with self.transaction(decision) as db:
            row=db.execute("SELECT state,token_digest FROM attempts WHERE ref=?",(ref,)).fetchone()
            require(row is not None and row[0] in old
                and (token_digest is None or row[1] is None or row[1]==token_digest),ERROR)
            db.execute("UPDATE attempts SET state=?,token_digest=COALESCE(?,token_digest) WHERE ref=?",(new,token_digest,ref))

    def state(self,ref,*,decision):
        _handle(ref)
        with self.transaction(decision) as db:
            row=db.execute("SELECT state,commitment,token_digest FROM attempts WHERE ref=?",(ref,)).fetchone()
            require(row is not None,ERROR)
            return dict(zip(("state","commitment","token_digest"),row))
