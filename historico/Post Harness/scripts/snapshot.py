#!/usr/bin/env python3
"""Inventario y snapshot fiel de un corpus UTF-8; no escribe en la fuente."""
import argparse, hashlib, json, platform, sys
from pathlib import Path
TEXT={'.md','.markdown','.txt','.rst','.json','.yaml','.yml','.csv','.tsv','.html','.xml'}
def digest(b): return hashlib.sha256(b).hexdigest()
def snapshot(root, out):
    root=Path(root).resolve(); out=Path(out).resolve()
    if out==root or root in out.parents: raise ValueError('El destino debe estar fuera del corpus')
    out.mkdir(parents=True,exist_ok=True); rows=[]; chunks=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file() and not p.is_symlink(): continue
        rel=p.relative_to(root).as_posix()
        if p.is_symlink():
            rows.append(dict(path=rel,included=False,reason='enlace simbólico: no se sigue'));continue
        b=p.read_bytes(); row=dict(path=rel,bytes=len(b),sha256=digest(b),mtime_ns=p.stat().st_mtime_ns)
        if p.suffix.lower() not in TEXT: row.update(included=False,reason='extensión no textual admitida')
        else:
            try: t=b.decode('utf-8'); assert '\x00' not in t
            except (UnicodeDecodeError,AssertionError):row.update(included=False,reason='no es texto UTF-8 sin NUL')
            else:
                row.update(included=True,lines=len(t.splitlines()))
                dest=out/'fuentes'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
                chunks.append(f'\n=== {rel} ===\n'+''.join(f'{i}: {l}\n' for i,l in enumerate(t.splitlines(),1)))
        rows.append(row)
    rev=digest(json.dumps([(r['path'],r.get('sha256'),r['included']) for r in rows],ensure_ascii=False).encode())
    inv=dict(root=str(root),revision=rev,python=sys.version,platform=platform.platform(),files=rows)
    (out/'inventario.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2))
    (out/'corpus_completo.txt').write_text(''.join(chunks))
    return inv
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('corpus');a.add_argument('destino');n=a.parse_args();r=snapshot(n.corpus,n.destino);print(json.dumps(dict(revision=r['revision'],incluidos=sum(x['included'] for x in r['files']),excluidos=sum(not x['included'] for x in r['files'])),indent=2))
