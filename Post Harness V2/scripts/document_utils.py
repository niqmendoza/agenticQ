#!/usr/bin/env python3
"""Navegador documental local, genérico y sólo lectura sobre la fuente.
Python >=3.10, biblioteca estándar. JSON por stdout; errores JSON con exit 2.
"""
import argparse, collections, hashlib, json, math, re, sqlite3, sys, unicodedata, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse
EXTENSIONS={'.md','.markdown','.txt','.rst','.json','.yaml','.yml','.csv','.tsv','.html','.xml'}
STOP=set('a al con de del el en es la las lo los o para por que se un una y the of to and in is for on with from'.split())
SCHEMA=1

def sha(b): return hashlib.sha256(b).hexdigest()
def norm(s): return ''.join(c for c in unicodedata.normalize('NFKD',s.casefold()) if not unicodedata.combining(c))
def words(s): return [w for w in re.findall(r'\w+',norm(s)) if len(w)>1 and w not in STOP]
def dump(x): return json.dumps(x,ensure_ascii=False,indent=2)+'\n'
def scan(root):
    rows=[];excluded=[]
    if not root.is_dir(): raise ValueError('El corpus no es un directorio')
    for p in sorted(root.rglob('*')):
        if p.is_symlink(): excluded.append({'path':p.relative_to(root).as_posix(),'reason':'symlink no seguido'});continue
        if not p.is_file():continue
        rel=p.relative_to(root).as_posix()
        if p.suffix.lower() not in EXTENSIONS:excluded.append({'path':rel,'reason':'extensión excluida'});continue
        b=p.read_bytes()
        try:
            text=b.decode('utf-8')
            if '\0' in text:raise ValueError()
        except (UnicodeDecodeError,ValueError):excluded.append({'path':rel,'reason':'no UTF-8 o NUL'});continue
        rows.append({'path':rel,'sha256':sha(b),'bytes':len(b),'text':text})
    return rows,excluded

def metadata(lines):
    # Preserva valores YAML crudos; no presume ontología ni interpreta YAML complejo.
    meta={};end=0
    if lines and lines[0].strip()=='---':
        for i,line in enumerate(lines[1:],1):
            if line.strip()=='---':end=i+1;break
        if end:
            meta['frontmatter_raw']='\n'.join(lines[:end])
            for line in lines[1:end-1]:
                m=re.match(r'^([\w-]+):\s*(.*)$',line)
                if m:meta[m[1]]=m[2].strip().strip('"\'')
    return meta,end

def sections(text,max_lines=40):
    lines=text.splitlines();meta,start=metadata(lines);head='Documento';begin=1;fence=None;spans=[]
    for i,line in enumerate(lines,1):
        if i<=start:continue
        fm=re.match(r'^\s*(`{3,}|~{3,})',line)
        if fm:
            c=fm[1][0]
            if fence==c:fence=None
            elif fence is None:fence=c
        if fence is None and re.match(r'^#{1,6}\s+',line):
            if begin<i:spans.append((begin,i-1,head))
            begin=i;head=re.sub(r'^#+\s+','',line)
    if lines:spans.append((begin,len(lines),head))
    result=[]
    for a,b,title in spans:
        while a<=b:
            e=min(a+max_lines-1,b);result.append((a,e,title,'\n'.join(lines[a-1:e])))
            if e==b:break
            a=e-3  # overlap verificable, sin perder líneas
    return meta,result

def links(path,text):
    for m in re.finditer(r'\[\[([^\]]+)\]\]|\[[^\]]*\]\(([^)]+)\)',text):
        raw=(m[1] or m[2]).split('|')[0];u=urlparse(raw)
        if u.scheme or raw.startswith('//'):continue
        yield {'target':unquote(raw.split('#')[0]),'fragment':unquote(raw.split('#',1)[1]) if '#' in raw else '', 'line':text[:m.start()].count('\n')+1,'kind':'wiki' if m[1] else 'markdown'}

def connect(db):
    c=sqlite3.connect(db);c.row_factory=sqlite3.Row
    return c

def index(root,db):
    root=Path(root).resolve();db=Path(db).resolve()
    if root==db or root in db.parents:raise ValueError('Guardar índice fuera del corpus')
    rows,excluded=scan(root);db.parent.mkdir(parents=True,exist_ok=True)
    c=connect(db)
    with c:
        c.execute('CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY,value TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS docs (path TEXT PRIMARY KEY,sha TEXT,bytes INTEGER,text TEXT,meta TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS chunks (path TEXT,start INTEGER,end INTEGER,section TEXT,text TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS links (path TEXT,data TEXT)')
        old=dict(c.execute('SELECT key,value FROM config').fetchall())
        if old and (old.get('root')!=str(root) or old.get('schema')!=str(SCHEMA)):raise ValueError('Índice de otra raíz/versión: use otra ruta de DB')
        previous={r['path']:r['sha'] for r in c.execute('SELECT path,sha FROM docs')};changed=0;removed=0
        current={r['path'] for r in rows}
        for p in set(previous)-current:
            for table in ('docs','chunks','links'):c.execute(f'DELETE FROM {table} WHERE path=?',(p,))
            removed+=1
        for r in rows:
            if previous.get(r['path'])==r['sha256']:continue
            changed+=1;meta,ch=sections(r['text'])
            for table in ('docs','chunks','links'):c.execute(f'DELETE FROM {table} WHERE path=?',(r['path'],))
            c.execute('INSERT INTO docs VALUES(?,?,?,?,?)',(r['path'],r['sha256'],r['bytes'],r['text'],json.dumps(meta,ensure_ascii=False)))
            c.executemany('INSERT INTO chunks VALUES(?,?,?,?,?)',[(r['path'],*x) for x in ch])
            c.executemany('INSERT INTO links VALUES(?,?)',[(r['path'],json.dumps(x,ensure_ascii=False)) for x in links(r['path'],r['text'])])
        revision=sha(json.dumps([(r['path'],r['sha256']) for r in rows],ensure_ascii=False).encode())
        cfg={'root':str(root),'revision':revision,'schema':str(SCHEMA),'excluded':json.dumps(excluded,ensure_ascii=False)}
        c.executemany('INSERT OR REPLACE INTO config VALUES(?,?)',cfg.items())
    result={'revision':revision,'documents':len(rows),'chunks':c.execute('SELECT count(*) FROM chunks').fetchone()[0], 'changed':changed,'removed':removed,'unchanged':len(rows)-changed,'excluded':excluded,'index_bytes':db.stat().st_size}
    c.close()
    return result

def checked(db):
    if not Path(db).is_file():raise ValueError('Falta índice: ejecutar index')
    c=connect(db);cfg=dict(c.execute('SELECT key,value FROM config').fetchall())
    if cfg.get('schema')!=str(SCHEMA):raise ValueError('Versión de índice incompatible')
    current,_=scan(Path(cfg['root']));actual={r['path']:r['sha256'] for r in current}
    stored={r['path']:r['sha'] for r in c.execute('SELECT path,sha FROM docs')}
    if actual!=stored:
        c.close()
        raise ValueError('Índice desactualizado (hash/altas/bajas): volver a ejecutar index')
    return c,cfg

def relations(c,path):
    docs=list(c.execute('SELECT path,meta FROM docs'));names=collections.defaultdict(set)
    for d in docs:
        p=Path(d['path']);m=json.loads(d['meta'])
        for key in [p.stem,d['path'],m.get('title','')]:
            if key:names[norm(key)].add(d['path'])
        for a in m.get('aliases','').strip('[]').split(','):
            if a.strip():names[norm(a.strip().strip('"\''))].add(d['path'])
    result=[]
    for r in c.execute('SELECT data FROM links WHERE path=?',(path,)):
        l=json.loads(r[0]);target=l['target']
        if l['kind']=='markdown':
            # Normalizar ../ sin permitir escapes de raíz ni resolver archivos externos.
            parts=[]
            for part in (Path(path).parent/target).parts:
                if part=='..':
                    if parts:parts.pop()
                    else:parts=['__outside__'];break
                elif part!='.':parts.append(part)
            candidate='/'.join(parts);matches={d['path'] for d in docs if d['path']==candidate}
        else:
            matches=names.get(norm(target),set())|names.get(norm(Path(target).stem),set())
        l.update(resolved=sorted(matches),ambiguous=len(matches)>1,missing=not matches);result.append(l)
    return result

def query(c,cfg,q,limit,offset,budget):
    terms=sorted(set(words(q)))
    if not terms:return {'query':q,'revision':cfg['revision'],'total_matches':0,'results':[],'missing_terms':[],'warning':'Consulta sin términos útiles'}
    docs={d['path']:d for d in c.execute('SELECT * FROM docs')};chunks=list(c.execute('SELECT * FROM chunks ORDER BY path,start'))
    bags=[];df=collections.Counter()
    for r in chunks:
        d=docs[r['path']];meta=json.loads(d['meta']);meta.pop('frontmatter_raw',None)
        bag=collections.Counter(words(r['text']));boost=collections.Counter(words(r['section']+' '+r['path']+' '+json.dumps(meta,ensure_ascii=False)))
        for w,n in boost.items():bag[w]+=2*n
        bags.append(bag);df.update(bag.keys())
    avg=sum(sum(b.values()) for b in bags)/max(1,len(bags));rank=[]
    for r,bag in zip(chunks,bags):
        size=sum(bag.values());score=0
        for t in terms:
            tf=bag[t]
            if tf:score+=math.log(1+(len(bags)-df[t]+.5)/(df[t]+.5))*tf*2.2/(tf+1.2*(.25+.75*size/max(1,avg)))
        if score:rank.append((score,r))
    rank.sort(key=lambda x:(-x[0],x[1]['path'],x[1]['start']))
    # Diversidad por documento en primera vuelta, resto luego; orden estable paginable.
    first=[];rest=[];seen=set()
    for score,r in rank:
        (rest if r['path'] in seen else first).append((score,r));seen.add(r['path'])
    rank=first+rest
    out={'query':q,'revision':cfg['revision'],'terms':terms,'missing_terms':[t for t in terms if not df[t]],'total_matches':len(rank),'offset':offset,'results':[],'next_offset':None,'truncated':False,'notices':['Ranking léxico OR, no prueba de exhaustividad. Ausencia de términos no demuestra ausencia funcional.','Metadatos crudos y enlaces no verifican vigencia ni resuelven contradicciones. Amplíe reglas, excepciones y dependencias.']}
    cursor=offset
    for score,r in rank[offset:offset+limit]:
        d=docs[r['path']];related=relations(c,r['path'])
        item={'path':r['path'],'sha256':d['sha'],'section':r['section'],'start':r['start'],'end':r['end'],'score':round(score,4),'metadata':json.loads(d['meta']),'excerpt':r['text'],'relations':related[:6],'relations_total':len(related),'relations_truncated':len(related)>6}
        trial=dict(out);trial['results']=out['results']+[item];trial['next_offset']=cursor+1;trial['truncated']=True
        if len(dump(trial))>budget:
            out['truncated']=True;out['next_offset']=cursor;out['notice_budget']='El próximo extracto no cabe completo. Aumente max-chars o use show por líneas.';break
        out['results'].append(item);cursor+=1
    if cursor<len(rank) and out['next_offset'] is None:out.update(next_offset=cursor,truncated=True)
    return out

def show(c,cfg,path,start,end,max_lines):
    r=c.execute('SELECT * FROM docs WHERE path=?',(path,)).fetchone()
    if not r:raise ValueError('Archivo no indexado; usar ruta relativa exacta')
    lines=r['text'].splitlines();explicit_end=end
    end=len(lines) if end is None else end
    if start<1 or (explicit_end is not None and end<start):raise ValueError('Rango inválido')
    e=min(end,start+max_lines-1,len(lines));a=min(start,len(lines)+1)
    return {'revision':cfg['revision'],'path':path,'sha256':r['sha'],'metadata':json.loads(r['meta']),'start':a,'end':e,'total_lines':len(lines),'text':'\n'.join(lines[a-1:e]),'truncated':e<min(end,len(lines)),'next_line':e+1 if e<min(end,len(lines)) else None,'requested_end':end,'beyond_eof':start>len(lines) or end>len(lines)}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',required=True);p.add_argument('--log-dir',help='Guarda invocación y salida exactas fuera del corpus')
    sub=p.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('index');s.add_argument('corpus')
    s=sub.add_parser('query');s.add_argument('query');s.add_argument('--limit',type=int,default=6);s.add_argument('--offset',type=int,default=0);s.add_argument('--max-chars',type=int,default=16000)
    s=sub.add_parser('show');s.add_argument('path');s.add_argument('--start',type=int,default=1);s.add_argument('--end',type=int);s.add_argument('--max-lines',type=int,default=60)
    s=sub.add_parser('links');s.add_argument('path');s.add_argument('--limit',type=int,default=20);s.add_argument('--offset',type=int,default=0)
    sub.add_parser('status')
    a=p.parse_args();code=0;started=datetime.now(timezone.utc).isoformat();tick=time.perf_counter()
    try:
        if a.cmd=='index':r=index(a.corpus,a.db)
        else:
            c,cfg=checked(a.db)
            if a.cmd in ('query','links') and (not 1<=a.limit<=100 or a.offset<0):raise ValueError('limit 1..100; offset >=0')
            if a.cmd=='query':
                if not 1000<=a.max_chars<=100000:raise ValueError('max-chars 1000..100000')
                r=query(c,cfg,a.query,a.limit,a.offset,a.max_chars)
            elif a.cmd=='show':
                if not 1<=a.max_lines<=500:raise ValueError('max-lines 1..500')
                r=show(c,cfg,a.path,a.start,a.end,a.max_lines)
            elif a.cmd=='links':
                items=relations(c,a.path);r={'path':a.path,'total':len(items),'results':items[a.offset:a.offset+a.limit],'next_offset':a.offset+a.limit if a.offset+a.limit<len(items) else None}
            else:r={'root':cfg['root'],'revision':cfg['revision'],'documents':c.execute('SELECT count(*) FROM docs').fetchone()[0],'chunks':c.execute('SELECT count(*) FROM chunks').fetchone()[0],'excluded':json.loads(cfg['excluded']),'fresh':True}
    except (ValueError,OSError,sqlite3.Error) as e:r={'error':str(e),'action':'Revisar argumentos o reindexar; no usar contexto obsoleto'};code=2
    output=dump(r)
    if a.log_dir:
        dest=Path(a.log_dir).resolve()
        # Logs son del harness local y no se escriben dentro del segundo cerebro.
        if a.cmd!='index':
            try:
                dbconn=connect(a.db);root=Path(dict(dbconn.execute('SELECT key,value FROM config'))['root'])
                if dest==root or root in dest.parents:raise ValueError('log-dir debe estar fuera del corpus')
            except (sqlite3.Error,KeyError):pass
        dest.mkdir(parents=True,exist_ok=True)
        n=len(list(dest.glob('*.invocation.json')))+1
        (dest/f'{n:03}.invocation.json').write_text(dump({'argv':sys.argv,'exit_code':code,'started_utc':started,'finished_utc':datetime.now(timezone.utc).isoformat(),'local_seconds':time.perf_counter()-tick}))
        (dest/f'{n:03}.result.json').write_text(output)
    print(output,end='');return code
if __name__=='__main__':sys.exit(main())
