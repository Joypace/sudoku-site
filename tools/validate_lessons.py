"""Build-time contract for the intentionally public learning subtree."""
import base64,hashlib,json,re,stat,sys,zlib,xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from urllib.parse import urlparse,parse_qs
SVG='http://www.w3.org/2000/svg'
TAGS={'svg','title','metadata','defs','style','g','path','rect','circle','ellipse','clipPath','filter','feGaussianBlur','image','use','text','tspan','set'}
ALL=511

def require(ok,why):
 if not ok:raise ValueError(why)
def unique_solution(grid):
 rows=[0]*9;cols=[0]*9;boxes=[0]*9;empty=[]
 for i,v in enumerate(map(int,grid)):
  r,c=divmod(i,9);b=r//3*3+c//3
  if not v:empty.append(i);continue
  bit=1<<(v-1);require(not ((rows[r]|cols[c]|boxes[b])&bit),'Conflicting givens');rows[r]|=bit;cols[c]|=bit;boxes[b]|=bit
 count=0
 def go(left):
  nonlocal count
  if not left:count+=1;return
  best=None;options=0;size=10
  for i in left:
   r,c=divmod(i,9);m=ALL&~(rows[r]|cols[c]|boxes[r//3*3+c//3]);n=m.bit_count()
   if n<size:best,options,size=i,m,n
   if n<=1:break
  if not size:return
  r,c=divmod(best,9);b=r//3*3+c//3;rest=[i for i in left if i!=best]
  while options and count<2:
   bit=options&-options;options-=bit;rows[r]|=bit;cols[c]|=bit;boxes[b]|=bit;go(rest);rows[r]^=bit;cols[c]^=bit;boxes[b]^=bit
 go(empty);require(count==1,'Practice puzzle must have exactly one solution')
def share_grid(url):
 p=urlparse(url);q=parse_qs(p.query,strict_parsing=True);require(p.scheme=='https' and p.netloc=='sudoku.joypace.com' and p.path=='/share/' and not p.fragment and set(q)=={'p'} and len(q['p'])==1,'Unexpected share URL')
 code=q['p'][0];require(bool(re.fullmatch('[A-Za-z0-9_-]{64}',code)),'Invalid share frame');b=base64.urlsafe_b64decode(code);require(b[:3]==b'SP\x01' and len(b)==48 and b[43]&15==0 and int.from_bytes(b[44:],'big')==zlib.crc32(b[:44]),'Invalid share checksum/version');digits=[(b[3+i//2]>>(4 if i%2==0 else 0))&15 for i in range(81)];require(all(v<=9 for v in digits),'Invalid share digit');return ''.join(map(str,digits))
def xwing(example):
 g=list(map(int,example['grid']));units=[set(range(r*9,r*9+9)) for r in range(9)]+[set(range(c,81,9)) for c in range(9)]+[{(r+dr)*9+c+dc for dr in range(3) for dc in range(3)} for r in (0,3,6) for c in (0,3,6)]
 cs={i:set(range(1,10))-{g[j] for u in units if i in u for j in u} for i,v in enumerate(g) if not v}
 require(all(len(opts)>1 for opts in cs.values()),'Advanced example still has a forced single')
 for unit in units:
  for digit in set(range(1,10))-{g[i] for i in unit}:require(sum(digit in cs.get(i,set()) for i in unit)>1,'Advanced example still has a forced single')
 d=example['digit'];require(d in range(1,10),'Invalid target digit');require(example['orientation'] in ['rows','columns'],'Unknown X-Wing orientation');row_based=example['orientation']=='rows';base=(lambda i:i//9) if row_based else (lambda i:i%9);cross=(lambda i:i%9) if row_based else (lambda i:i//9);bases=example['bases'];covers=example['covers'];require(len(set(bases))==2 and len(set(covers))==2 and all(i in range(9) for i in bases+covers),'Invalid base/cover units');corners=set()
 for b in bases:
  live={i for i in cs if base(i)==b and d in cs[i]};require(len(live)==2 and {cross(i) for i in live}==set(covers),'X-Wing is not present in the original notes');corners|=live
 require(set(example['corners'])==corners,'Wrong four corners');targets={i for i in cs if base(i) not in bases and cross(i) in covers and d in cs[i]};require(targets and set(example['targets'])==targets,'Incorrect or incomplete X-Wing eliminations');branches=example['branches'];require(len(branches)==2 and {q[0] for q in branches}=={i for i in corners if base(i)==bases[0]},'Branches must exhaust the first base unit')
 for first,forced in branches:
  require(first in corners and forced in corners and base(first)!=base(forced) and cross(first)!=cross(forced),'Wrong forced second placement')
PROOFS={'x-wing':xwing}
def check_svg(file,scenario,example):
 raw=file.read_text();without_declaration=re.sub(r'^\s*<\?xml\s[^?]*\?>','',raw,count=1);require('<?' not in without_declaration,'SVG processing instructions are forbidden');require('<!DOCTYPE' not in raw.upper() and '<!ENTITY' not in raw.upper(),'External XML declarations are forbidden');root=ET.fromstring(raw);require(root.tag=='{'+SVG+'}svg','Not a standalone SVG');require(float(root.attrib.get('data-duration',0))>0,'Not an animation')
 for e in root.iter():
  require(e.tag.startswith('{'+SVG+'}') and e.tag.rsplit('}',1)[-1] in TAGS,'Unsupported SVG element');tag=e.tag.rsplit('}',1)[-1]
  for name,value in e.attrib.items():
   local=name.rsplit('}',1)[-1];require(local not in ['base','style'],'Inline SVG base/style attributes are forbidden');require('\\' not in value,'SVG attribute escaping is forbidden');require(not local.lower().startswith('on'),'SVG event handler forbidden');require('javascript:' not in value.lower(),'Executable SVG attribute')
   if local=='href':require(bool(re.fullmatch(r'#[A-Za-z_][A-Za-z0-9_.:-]*',value)) or bool(re.fullmatch(r'data:image/(?:png|webp);base64,[A-Za-z0-9+/=]+',value)),'External or executable SVG resource')
   for target in re.findall(r'url\(\s*["\']?([^\)"\']+)',value,flags=re.IGNORECASE):require(target.startswith('#'),'External SVG attribute resource')
  if tag=='set':
   require(set(e.attrib)<={'attributeName','to','begin','dur','fill'} and e.attrib.get('attributeName')=='display' and e.attrib.get('to')=='inline' and e.attrib.get('fill') in ['freeze','remove'],'Unsupported SVG animation target')
   require(bool(re.fullmatch(r'\d+(?:\.\d+)?s',e.attrib.get('begin',''))),'Unsupported animation trigger')
   if 'dur' in e.attrib:require(bool(re.fullmatch(r'\d+(?:\.\d+)?s',e.attrib['dur'])),'Unsupported animation duration')
  if tag=='style':
   css=e.text or '';require('\\' not in css and '/*' not in css,'Unsupported SVG CSS escaping');faces=re.findall(r'@font-face\{([^{}]+)\}',css);require(''.join('@font-face{'+f+'}' for f in faces)==css,'Only exporter font declarations are permitted')
   for face in faces:require(bool(re.fullmatch(r'font-family:"[^"\\<>]+";font-weight:[1-9]00;src:url\("data:font/ttf;base64,[A-Za-z0-9+/=]+"\) format\("(?:truetype|opentype)"\)',face)),'Unsupported font source')
 meta=root.find('{'+SVG+'}metadata');require(meta is not None and meta.text,'Missing App export provenance');source=json.JSONDecoder().raw_decode(meta.text)[0];require(source.get('productDirty') is False and bool(re.fullmatch('[a-f0-9]{40}',source.get('app',''))) and bool(re.fullmatch('[a-f0-9]{40}',source.get('content',''))),'Unqualified App source');sha=hashlib.sha256(scenario.read_bytes()).hexdigest();require(source.get('story',{}).get('sha256')==sha==example.get('scenarioSHA256'),'Scenario/SVG provenance mismatch')
def validate(root):
 directory=root/'learn'
 if not directory.exists() and not directory.is_symlink():return []
 actual=[]
 def walk(folder,prefix=''):
  require(not folder.is_symlink() and folder.is_dir(),'Public lesson directory must not be a symlink')
  for file in folder.iterdir():
   require(not file.is_symlink(),'No symlinks in public lessons');require(bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',file.name)),'Unsafe public filename');name=prefix+file.name
   if file.is_dir():walk(file,name+'/')
   else:require(file.is_file(),'Unexpected public file type');actual.append(name)
 walk(directory)
 manifest=json.loads((directory/'manifest.json').read_text());require(manifest.get('schema')==1 and isinstance(manifest.get('lessons'),list),'Invalid lesson manifest');expected={'index.html','learn.css','learn.js','manifest.json'};slugs=set();dates=set()
 for lesson in manifest['lessons']:
  slug=lesson['slug'];require(bool(re.fullmatch(r'[a-z][a-z0-9-]{1,70}',slug)) and slug not in {'index','learn','manifest'} and slug not in slugs,'Reserved/duplicate/unsafe lesson slug');slugs.add(slug);published=date.fromisoformat(lesson['published']);require(published not in dates,'At most one technique per date');dates.add(published);require(lesson.get('title') and lesson.get('description'),'Missing public lesson text');items=lesson['examples'];require(isinstance(items,list) and 3<=len(items)<=5,'Each technique needs 3–5 examples');folder=directory/slug;expected|={slug+'/index.html',slug+'/examples.json'};examples=json.loads((folder/'examples.json').read_text());require(len(examples)==len(items),'Example count mismatch');require(slug in PROOFS,'Technique requires a validated proof rule before publication')
  grids=set()
  for n,(entry,example) in enumerate(zip(items,examples),1):
   stem=f'example-{n}';require(entry.get('id')==stem and example.get('id')==stem and example.get('animation')==stem+'.svg','Example ID mismatch');grid=example['grid'];require(grid not in grids,'Each example must use a different starting puzzle');grids.add(grid);require(bool(re.fullmatch('[0-9]{81}',grid)),'Invalid starting grid');require(share_grid(example['shareURL'])==grid,'Share link does not open the animated starting clues');unique_solution(grid);PROOFS[slug](example)
   scenario=folder/(stem+'.json');data=json.loads(scenario.read_text());require(data['grid']==grid and isinstance(data.get('setup'),list) and data['setup']==[],'No hidden setup may precede a shared example')
   if slug=='x-wing':require(data.get('expected',{}).get('initialStatus')=='dilemma','Missing initial Dilemma runtime assertion')
   check_svg(folder/(stem+'.svg'),scenario,example);expected|={slug+'/'+stem+'.json',slug+'/'+stem+'.svg'}
 require(set(actual)==expected,'Unapproved or missing public lesson files: '+str(set(actual)^expected));return sorted('learn/'+p for p in actual)
if __name__=='__main__':
 try:print(json.dumps(validate(Path(sys.argv[1]).resolve())))
 except Exception as error:print(str(error),file=sys.stderr);sys.exit(1)
