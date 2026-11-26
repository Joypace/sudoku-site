"""Build-time contract for the intentionally public learning subtree."""
import base64,hashlib,json,re,stat,sys,zlib,xml.etree.ElementTree as ET
import importlib.util
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
def position(example):
 g=list(map(int,example['grid']));units=[set(range(r*9,r*9+9)) for r in range(9)]+[set(range(c,81,9)) for c in range(9)]+[{(r+dr)*9+c+dc for dr in range(3) for dc in range(3)} for r in (0,3,6) for c in (0,3,6)]
 cs={i:set(range(1,10))-{g[j] for u in units if i in u for j in u} for i,v in enumerate(g) if not v}
 return g,units,cs
def advanced_position(example):
 g,units,cs=position(example)
 require(all(len(opts)>1 for opts in cs.values()),'Advanced example still has a forced single')
 for unit in units:
  for d in set(range(1,10))-{g[i] for i in unit}:require(sum(d in cs.get(i,set()) for i in unit)>1,'Advanced example still has a forced single')
 return g,units,cs
def naked_pair(example):
 g,units,cs=advanced_position(example)
 kind,n=example['unit'],example['unitIndex'];require(kind in ['row','column','box'] and type(n)==int and n in range(9),'Invalid pair unit');unit=units[{'row':0,'column':9,'box':18}[kind]+n]
 pair=example['pair'];digits=example['digits'];require(len(pair)==2 and len(set(pair))==2 and all(type(i)==int and i in unit for i in pair),'Pair needs two distinct cells in the named unit');require(len(digits)==2 and len(set(digits))==2 and all(type(d)==int and d in range(1,10) for d in digits),'Pair needs two distinct digits')
 require(all(cs.get(i)==set(digits) for i in pair),'Both pair cells must have exactly the same two candidates')
 targets={(i,d) for i in unit if i not in pair for d in digits if d in cs.get(i,set())};claimed=[tuple(q) for q in example['targets']];require(targets and len(claimed)==len(set(claimed)) and set(claimed)==targets,'Incorrect or incomplete pair eliminations')
 a,b=pair;x,y=digits;branches=example['branches'];require(len(branches)==2 and {tuple(map(tuple,q)) for q in branches}=={((a,x),(b,y)),((a,y),(b,x))},'Pair trials must exhaust both candidate assignments')
def xwing(example):
 g,units,cs=advanced_position(example)
 d=example['digit'];require(d in range(1,10),'Invalid target digit');require(example['orientation'] in ['rows','columns'],'Unknown X-Wing orientation');row_based=example['orientation']=='rows';base=(lambda i:i//9) if row_based else (lambda i:i%9);cross=(lambda i:i%9) if row_based else (lambda i:i//9);bases=example['bases'];covers=example['covers'];require(len(set(bases))==2 and len(set(covers))==2 and all(i in range(9) for i in bases+covers),'Invalid base/cover units');corners=set()
 for b in bases:
  live={i for i in cs if base(i)==b and d in cs[i]};require(len(live)==2 and {cross(i) for i in live}==set(covers),'X-Wing is not present in the original notes');corners|=live
 require(set(example['corners'])==corners,'Wrong four corners');targets={i for i in cs if base(i) not in bases and cross(i) in covers and d in cs[i]};require(targets and set(example['targets'])==targets,'Incorrect or incomplete X-Wing eliminations');branches=example['branches'];require(len(branches)==2 and {q[0] for q in branches}=={i for i in corners if base(i)==bases[0]},'Branches must exhaust the first base unit')
 for first,forced in branches:
  require(first in corners and forced in corners and base(first)!=base(forced) and cross(first)!=cross(forced),'Wrong forced second placement')
def naked_single(example):
 g,units,cs=position(example);i,d=example['cell'],example['digit'];require(type(i)==int and i in range(81) and type(d)==int and d in range(1,10),'Invalid naked-single choice');require(cs.get(i)=={d},'Naked Single must have exactly one candidate')
 witnesses=example['exclusions'];require(all(type(w['digit'])==int for w in witnesses),'Naked-single witness digits must be integers');others=set(range(1,10))-{d};require(len(witnesses)==8 and {x['digit'] for x in witnesses}==others,'Every other digit needs a clue witness');peers=set().union(*(u for u in units if i in u))-{i}
 for w in witnesses:
  j=w['given'];require(type(j)==int and j in peers and g[j]==w['digit'],'Naked-single exclusion must be an original peer clue')
def hidden_pair(example):
 g,units,cs=advanced_position(example);kind,n=example['unit'],example['unitIndex'];require(kind in ['row','column','box'] and type(n)==int and n in range(9),'Invalid hidden-pair unit');unit=units[{'row':0,'column':9,'box':18}[kind]+n];pair=example['pair'];ds=example['digits']
 require(len(pair)==2 and len(set(pair))==2 and all(type(i)==int and i in unit for i in pair),'Hidden Pair needs two distinct cells in its unit');require(len(ds)==2 and len(set(ds))==2 and all(type(d)==int and d in range(1,10) for d in ds),'Hidden Pair needs two distinct digits')
 for d in ds:require({i for i in unit if d in cs.get(i,set())}==set(pair),'Each hidden-pair digit must occur only in the same two cells')
 require(all(len(q)==2 and all(type(v)==int for v in q) for q in example['targets']),'Hidden Pair target cells and digits must be integers')
 require(all(len(q)==2 and all(len(choice)==2 and all(type(v)==int for v in choice) for choice in q) for q in example['branches']),'Hidden Pair trial cells and digits must be integers')
 targets={(i,d) for i in pair for d in cs[i]-set(ds)};claimed=[tuple(q) for q in example['targets']];require(targets and len(claimed)==len(set(claimed)) and set(claimed)==targets,'Hidden Pair removes exactly the other notes from its own cells');a,b=pair;x,y=ds
 require(len(example['branches'])==2 and {tuple(map(tuple,q)) for q in example['branches']}=={((a,x),(b,y)),((a,y),(b,x))},'Hidden Pair trials must exhaust both assignments')
def claiming(example):
 g,units,cs=advanced_position(example);box=example['boxIndex'];kind=example['line'];n=example['lineIndex'];d=example['digit'];require(type(box)==int and box in range(9) and kind in ['row','column'] and type(n)==int and n in range(9),'Invalid claiming line/box');require(type(d)==int and d in range(1,10),'Invalid claiming digit')
 line=units[(0 if kind=='row' else 9)+n];places={i for i in line if d in cs.get(i,set())};ps=example['positions'];require(all(type(i)==int for i in ps) and len(places) in [2,3] and len(ps)==len(set(ps)) and set(ps)==places,'Claiming must show every candidate on the source line');cells=units[18+box];require(places<=cells,'All line candidates must be inside the named box');targets={i for i in cells-line if d in cs.get(i,set())};ts=example['targets'];require(targets and all(type(i)==int for i in ts) and len(ts)==len(set(ts)) and set(ts)==targets,'Claiming removes exactly the box candidates outside its source line')
def hidden_single(example):
 g=list(map(int,example['grid']));kind=example['unit'];n=example['unitIndex'];d=example['digit'];target=example['cell']
 require(kind in ['row','column','box'] and type(n)==int and n in range(9),'Invalid hidden-single unit')
 require(type(d)==int and d in range(1,10) and type(target)==int and target in range(81),'Invalid hidden-single choice')
 units=[set(range(r*9,r*9+9)) for r in range(9)]+[set(range(c,81,9)) for c in range(9)]+[{(r+dr)*9+c+dc for dr in range(3) for dc in range(3)} for r in (0,3,6) for c in (0,3,6)]
 peers=lambda i:set().union(*(u for u in units if i in u))-{i}
 unit=units[{'row':0,'column':9,'box':18}[kind]+n];cs={i:set(range(1,10))-{g[j] for j in peers(i)} for i,v in enumerate(g) if not v}
 require(target in unit and not g[target] and d not in {g[i] for i in unit},'Hidden-single digit must be missing in its unit')
 require({i for i in unit if d in cs.get(i,set())}=={target},'Hidden single must have exactly one place in the named unit')
 require(len(cs[target])>1 and example['candidates']==sorted(cs[target]),'Hidden single must show exact multiple cell candidates')
 exclusions=example['exclusions'];others={i for i in unit if not g[i] and i!=target}
 require(len(exclusions)==len(others) and {x['cell'] for x in exclusions}==others,'Every other empty unit cell needs an exclusion witness')
 for item in exclusions:
  i,j=item['cell'],item['given'];require(type(j)==int and j in range(81) and j in peers(i) and g[j]==d,'Exclusion witness must be an original peer clue of the target digit')

def pointing(example):
 g,units,cs=advanced_position(example);box=example['boxIndex'];kind=example['line'];n=example['lineIndex'];d=example['digit']
 require(type(box)==int and box in range(9) and kind in ['row','column'] and type(n)==int and n in range(9),'Invalid pointing box/line');require(type(d)==int and d in range(1,10),'Invalid pointing digit')
 cells=units[18+box];places={i for i in cells if d in cs.get(i,set())};claimed=example['positions'];require(all(type(i)==int for i in claimed),'Pointing positions must be cell indices');require(len(places) in [2,3] and len(claimed)==len(set(claimed)) and set(claimed)==places,'Pointing must show every candidate in the box')
 line=units[(0 if kind=='row' else 9)+n];require(all(type(i)==int for i in example['targets']),'Pointing targets must be cell indices');require(places<=line,'Box candidates must all lie on the named line');targets={i for i in line-cells if d in cs.get(i,set())};require(targets and len(example['targets'])==len(set(example['targets'])) and set(example['targets'])==targets,'Incorrect or incomplete pointing eliminations')
def pointing_animation(data,example):
 ps=example['positions'];d=example['digit'];box=example['boxIndex'];checks=data.get('expected',{});reveal=data.get('presentation',{}).get('choiceReveal',{})
 require(checks.get('boards')==len(ps)+1 and checks.get('slotFills')==[[slot,i//9,i%9,d] for slot,i in enumerate(ps,1)] and checks.get('validSlots')==list(range(len(ps)+1)),'Pointing animation must test every box placement on valid boards')
 require(checks.get('overlays')==[[slot,0] for slot in range(1,len(ps)+1)] and checks.get('notes')==[[i//9,i%9,d,False] for i in example['targets']],'Pointing animation must overlay every try and remove only proved targets')
 require(checks.get('revealFrameCount')==1 and checks.get('revealLabelCount')==len(ps) and reveal.get('frames')==[[box//3*3,box%3*3,3,3]] and reveal.get('labels')==[[i//9,i%9,d] for i in ps],'Pointing reveal must show the complete box choice set')

def naked_single_animation(data,e):
 i,d=e['cell'],e['digit'];q=[i//9,i%9,d];checks=data.get('expected',{});reveal=data.get('presentation',{}).get('choiceReveal',{})
 require(checks.get('initialStatus')=='definite' and checks.get('initialSingle')==q,'Naked Single must assert its actual forced starting choice')
 require(checks.get('boards')==1 and checks.get('slotFills')==[[0,*q]] and checks.get('fills')==[q] and checks.get('validSlots')==[0] and checks.get('overlays')==[],'Naked Single animation must fill its forced choice without a trial')
 require(reveal.get('frames')==[[i//9,i%9,1,1]] and reveal.get('labels')==[q],'Naked Single reveal must show its own cell and sole candidate')
 actions=[f for f in data['frames'] if f['do'] not in ['hover','depart','hide']]
 require(len(actions)==1 and actions[0]['do']=='tap' and actions[0].get('count')==2 and actions[0].get('at')=={'part':'cell','cell':q[:2]},'Naked Single capture must use one cell-centered forced double tap')
def hidden_pair_animation(data,e):
 ds=e['digits'];pair=e['pair'];kind=e['unit'];n=e['unitIndex'];checks=data.get('expected',{});reveal=data.get('presentation',{}).get('choiceReveal',{});geometry={'row':[n,0,1,9],'column':[0,n,9,1],'box':[n//3*3,n%3*3,3,3]}[kind]
 require(checks.get('boards')==3 and checks.get('slotFills')==[[slot,i//9,i%9,d] for slot,branch in enumerate(e['branches'],1) for i,d in branch] and checks.get('validSlots')==[0,1,2],'Hidden Pair animation must test both assignments on valid copied boards')
 notes=[[i//9,i%9,d,False] for i,d in e['targets']]+[[i//9,i%9,d,True] for i in pair for d in ds]
 require(checks.get('overlays')==[[1,0],[2,0]] and checks.get('notes')==notes,'Hidden Pair must overlay both tries and retain the reserved pair digits')
 require(checks.get('revealFrameCount')==1 and checks.get('revealLabelCount')==4 and reveal.get('frames')==[geometry] and reveal.get('labels')==[[i//9,i%9,d] for i in pair for d in ds],'Hidden Pair reveal must show the full unit and both digits in both cells')
def claiming_animation(data,e):
 ps=e['positions'];d=e['digit'];kind=e['line'];n=e['lineIndex'];checks=data.get('expected',{});reveal=data.get('presentation',{}).get('choiceReveal',{});geometry=[n,0,1,9] if kind=='row' else [0,n,9,1]
 require(checks.get('boards')==len(ps)+1 and checks.get('slotFills')==[[slot,i//9,i%9,d] for slot,i in enumerate(ps,1)] and checks.get('validSlots')==list(range(len(ps)+1)),'Claiming animation must test every source-line placement')
 require(checks.get('overlays')==[[slot,0] for slot in range(1,len(ps)+1)] and checks.get('notes')==[[i//9,i%9,d,False] for i in e['targets']],'Claiming must overlay every try and remove only proved box targets')
 require(checks.get('revealFrameCount')==1 and checks.get('revealLabelCount')==len(ps) and reveal.get('frames')==[geometry] and reveal.get('labels')==[[i//9,i%9,d] for i in ps],'Claiming reveal must show the complete source line')
PROOFS={'x-wing':xwing,'hidden-single':hidden_single,'naked-pair':naked_pair,'pointing':pointing,'naked-single':naked_single,'hidden-pair':hidden_pair,'claiming':claiming}

def _load_sibling(name):
 spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
INTERMEDIATE=('naked-triple','hidden-triple','swordfish','xy-wing','xyz-wing','w-wing','skyscraper','two-string-kite','empty-rectangle')
_intermediate=_load_sibling('intermediate_proofs');_stories=_load_sibling('intermediate_stories')
for _slug in INTERMEDIATE:PROOFS[_slug]=lambda example,slug=_slug:_intermediate.validate_pattern(slug,example)
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
 manifest=json.loads((directory/'manifest.json').read_text())
 if 'curriculum' in manifest:
  require(manifest['curriculum']=='curriculum.json' and (directory/'curriculum.json').is_file(),'Missing canonical curriculum')
 require(manifest.get('schema')==1 and isinstance(manifest.get('lessons'),list),'Invalid lesson manifest');expected={'index.html','learn.css','learn.js','manifest.json'};expected|={'curriculum.json'} if 'curriculum' in manifest else set();slugs=set()
 for lesson in manifest['lessons']:
  slug=lesson['slug'];require(bool(re.fullmatch(r'[a-z][a-z0-9-]{1,70}',slug)) and slug not in {'index','learn','manifest'} and slug not in slugs,'Reserved/duplicate/unsafe lesson slug');slugs.add(slug);published=date.fromisoformat(lesson['published']);require(lesson.get('title') and lesson.get('description'),'Missing public lesson text');items=lesson['examples'];require(isinstance(items,list) and 3<=len(items)<=5,'Each technique needs 3–5 examples');folder=directory/slug;expected|={slug+'/index.html',slug+'/examples.json'};examples=json.loads((folder/'examples.json').read_text());require(len(examples)==len(items),'Example count mismatch');require(slug in PROOFS,'Technique requires a validated proof rule before publication')
  grids=set()
  for n,(entry,example) in enumerate(zip(items,examples),1):
   stem=f'example-{n}';require(entry.get('id')==stem and example.get('id')==stem and example.get('animation')==stem+'.svg','Example ID mismatch');grid=example['grid'];require(grid not in grids,'Each example must use a different starting puzzle');grids.add(grid);require(bool(re.fullmatch('[0-9]{81}',grid)),'Invalid starting grid');require(share_grid(example['shareURL'])==grid,'Share link does not open the animated starting clues');unique_solution(grid);PROOFS[slug](example)
   scenario=folder/(stem+'.json');data=json.loads(scenario.read_text());require(data['grid']==grid and isinstance(data.get('setup'),list) and data['setup']==[],'No hidden setup may precede a shared example')
   if slug in ['x-wing','naked-pair','pointing','hidden-pair','claiming']:require(data.get('expected',{}).get('initialStatus')=='dilemma','Missing initial Dilemma runtime assertion')
   if slug=='hidden-single':
    i,d,n=example['cell'],example['digit'],example['unitIndex'];kind=example['unit'];choice=[i//9,i%9,d];checks=data.get('expected',{});reveal=data.get('presentation',{}).get('choiceReveal',{});geometry={'row':[n,0,1,9],'column':[0,n,9,1],'box':[n//3*3,n%3*3,3,3]}[kind]
    require(checks.get('initialStatus')=='definite' and checks.get('initialSingle')==choice,'Missing forced-choice initial runtime assertion')
    require(data.get('style')=='chill' and checks.get('slotFills')==[[0,*choice]] and checks.get('validSlots')==[0] and checks.get('fills')==[choice] and checks.get('boards')==1 and checks.get('overlays')==[],'Hidden-single capture must assert its actual fill and valid original board')
    require(reveal.get('frames')==[geometry] and reveal.get('labels')==[choice] and reveal.get('start')==500,'Hidden-single highlight must reveal the complete named unit and target candidate')
    actions=[f for f in data['frames'] if f['do'] not in ['hover','depart','hide']]
    require(len(actions)==1 and actions[0]['do']=='tap' and actions[0].get('count')==2 and actions[0].get('at')=={'part':'cell','cell':choice[:2]},'Hidden-single capture must use one cell-centered forced double tap')
   if slug=='pointing':pointing_animation(data,example)
   if slug=='naked-single':naked_single_animation(data,example)
   if slug=='hidden-pair':hidden_pair_animation(data,example)
   if slug=='claiming':claiming_animation(data,example)
   if slug in INTERMEDIATE:_stories.validate_story(data,example)
   check_svg(folder/(stem+'.svg'),scenario,example);expected|={slug+'/'+stem+'.json',slug+'/'+stem+'.svg'}
 if 'curriculum' in manifest:_load_sibling('lesson_catalogue').validate_curriculum(json.loads((directory/'curriculum.json').read_text()),manifest)
 require(set(actual)==expected,'Unapproved or missing public lesson files: '+str(set(actual)^expected));return sorted('learn/'+p for p in actual)
if __name__=='__main__':
 try:print(json.dumps(validate(Path(sys.argv[1]).resolve())))
 except Exception as error:print(str(error),file=sys.stderr);sys.exit(1)
