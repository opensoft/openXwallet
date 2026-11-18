"""Explicitly initialized, retained one-attempt staging state; never create on open."""
from contextlib import contextmanager,closing
import os
from pathlib import Path
import sqlite3
import stat
import time
from workload_factory_binding.evidence import BindingError,canonical,integer,require
from ..config import _handle
from ..github_bootstrap.common import document

ERROR="hosted-stage-refused"
DB="staging.sqlite"
SCHEMA=("CREATE TABLE metadata (version INTEGER NOT NULL, kind TEXT NOT NULL, highwater INTEGER NOT NULL)",
        "CREATE TABLE stages (ref TEXT PRIMARY KEY, scope BLOB NOT NULL, state TEXT NOT NULL, unit BLOB, generation BLOB, status_reads INTEGER NOT NULL, started INTEGER NOT NULL, deadline INTEGER NOT NULL, lease BLOB)")
EDGES={"reserved":{"registered","indeterminate","refused"},"registered":{"start-consumed","indeterminate","refused"},
       "start-consumed":{"running","indeterminate","refused"},"running":{"stopped","indeterminate"}}


def _main_identity(path):
    a,b=path.lstat(),(path/DB).lstat()
    require(stat.S_ISDIR(a.st_mode) and stat.S_ISREG(b.st_mode) and b.st_nlink==1
            and all(x.st_uid==os.geteuid() and not x.st_mode&0o077 for x in (a,b)),ERROR)
    return a.st_dev,a.st_ino,b.st_dev,b.st_ino


def store_identity(directory):
    path=Path(directory).absolute();require(path.resolve()==path,ERROR)
    identity=_main_identity(path)
    for suffix in ("-journal","-wal","-shm"):
        try:
            x=(path/(DB+suffix)).lstat()
        except FileNotFoundError:
            continue  # A concurrent SQLite DELETE-mode commit can retire its journal.
        require(suffix=="-journal" and stat.S_ISREG(x.st_mode) and x.st_nlink==1
                and x.st_uid==os.geteuid() and not x.st_mode&0o077,ERROR)
    require(_main_identity(path)==identity,ERROR)
    return identity


class StageStore:
    @classmethod
    def initialize(cls,directory,*,kind):
        try:
            require(kind in ("controller","host"),ERROR);p=Path(directory).absolute();p.mkdir(mode=0o700)
            fd=os.open(p/DB,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
            with closing(sqlite3.connect(p/DB)) as db,db:
                db.execute("PRAGMA synchronous=FULL")
                for sql in SCHEMA:db.execute(sql)
                db.execute("INSERT INTO metadata VALUES (1,?,0)",(kind,))
            fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(fd)
            finally:os.close(fd)
            return store_identity(p)
        except Exception:raise BindingError(ERROR) from None

    def __init__(self,directory,*,identity,kind):
        self.directory,self.identity,self.kind=Path(directory).absolute(),identity,kind
        try:require(kind in ("controller","host") and store_identity(self.directory)==identity,ERROR)
        except Exception:raise BindingError(ERROR) from None

    @contextmanager
    def transaction(self,decision):
        db=None
        try:
            decision.now();require(store_identity(self.directory)==self.identity,ERROR)
            db=sqlite3.connect((self.directory/DB).as_uri()+"?mode=rw",uri=True,
                timeout=min(1,decision.remaining()),isolation_level=None)
            end=time.monotonic()+min(1,decision.remaining());db.set_progress_handler(lambda:int(time.monotonic()>=end),100)
            db.execute("PRAGMA synchronous=FULL");require(db.execute("PRAGMA journal_mode").fetchone()==("delete",),ERROR)
            actual=tuple(x[0] for x in db.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name"))
            require(actual==tuple(sorted(SCHEMA,key=lambda x:x.split()[2])),ERROR)
            db.execute("BEGIN IMMEDIATE");rows=db.execute("SELECT version,kind,highwater FROM metadata").fetchall();now=decision.now()
            require(len(rows)==1 and rows[0][:2]==(1,self.kind) and integer(rows[0][2]) and now>=rows[0][2],ERROR)
            db.execute("UPDATE metadata SET highwater=?",(now,));db.execute("SAVEPOINT business");failed=True
            try:
                yield db
                decision.now();require(store_identity(self.directory)==self.identity,ERROR);failed=False
            finally:
                if failed:db.execute("ROLLBACK TO business")
                db.execute("RELEASE business");db.execute("COMMIT")
        except Exception:raise BindingError(ERROR) from None
        finally:
            if db is not None:
                if db.in_transaction:db.rollback()
                db.close()

    def reserve(self,ref,scope,*,decision,expires_at=None):
        _handle(ref);raw=canonical(scope);require(type(scope) is dict and len(raw)<=16384,ERROR)
        with self.transaction(decision) as db:
            row=db.execute("SELECT scope FROM stages WHERE ref=?",(ref,)).fetchone()
            if row is not None:require(row[0]==raw,ERROR);return False
            require(db.execute("SELECT count(*) FROM stages").fetchone()[0]<256,ERROR)
            now=decision.now();expiry=now+60 if expires_at is None else expires_at
            require(integer(expiry) and now<expiry,ERROR)
            db.execute("INSERT INTO stages VALUES (?,?,'reserved',NULL,NULL,0,?,?,NULL)",(ref,raw,now,min(now+60,expiry)));return True

    def read(self,ref,*,decision):
        _handle(ref)
        with self.transaction(decision) as db:
            row=db.execute("SELECT scope,state,unit,generation,deadline,status_reads,lease FROM stages WHERE ref=?",(ref,)).fetchone()
            require(row is not None,ERROR)
            return {"scope":document(row[0]),"state":row[1],"unit":document(row[2]) if row[2] is not None else None,
                    "generation":document(row[3]) if row[3] is not None else None,"deadline":row[4],"status_reads":row[5],
                    "lease":document(row[6]) if row[6] is not None else None}

    def transition(self,ref,old,new,*,decision,unit=None,generation=None):
        _handle(ref);require(new in EDGES.get(old,set()),ERROR)
        raw_unit=canonical(unit) if unit is not None else None;raw_generation=canonical(generation) if generation is not None else None
        require(all(v is None or len(v)<=16384 for v in (raw_unit,raw_generation)),ERROR)
        with self.transaction(decision) as db:
            row=db.execute("SELECT state,unit,generation FROM stages WHERE ref=?",(ref,)).fetchone();require(row and row[0]==old,ERROR)
            require(raw_unit is None or row[1] is None or row[1]==raw_unit,ERROR)
            require(raw_generation is None or row[2] is None or row[2]==raw_generation,ERROR)
            changed=db.execute("UPDATE stages SET state=?,unit=COALESCE(unit,?),generation=COALESCE(generation,?) WHERE ref=? AND state=?",
                (new,raw_unit,raw_generation,ref,old));require(changed.rowcount==1,ERROR)

    def status_read(self,ref,*,decision):
        _handle(ref)
        with self.transaction(decision) as db:
            row=db.execute("SELECT status_reads,deadline FROM stages WHERE ref=?",(ref,)).fetchone()
            require(row is not None and 0<=row[0]<6 and decision.now()<row[1],ERROR)
            decision.clip(row[1]);db.execute("UPDATE stages SET status_reads=status_reads+1 WHERE ref=?",(ref,))
        return self.read(ref,decision=decision)

    def bind_lease(self,ref,lease,*,decision):
        _handle(ref);raw=canonical(lease);require(type(lease) is dict and len(raw)<=16384 and integer(lease.get("expires_at")),ERROR)
        with self.transaction(decision) as db:
            row=db.execute("SELECT lease,deadline FROM stages WHERE ref=?",(ref,)).fetchone()
            require(row is not None and (row[0] is None or row[0]==raw) and decision.now()<lease["expires_at"],ERROR)
            db.execute("UPDATE stages SET lease=COALESCE(lease,?),deadline=MIN(deadline,?) WHERE ref=?",(raw,lease["expires_at"],ref))
            decision.clip(min(row[1],lease["expires_at"]))

    def known(self,ref,scope,*,decision):
        _handle(ref)
        with self.transaction(decision) as db:
            row=db.execute("SELECT scope FROM stages WHERE ref=?",(ref,)).fetchone()
            require(row is None or row[0]==canonical(scope),ERROR);return row is not None
