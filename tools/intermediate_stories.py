"""Bind intermediate demonstrations to exhaustive native copied-board trials."""
def require(ok,why):
 if not ok:raise ValueError(why)
def validate_story(data,e):
 require(data.get('style')=='chill' and data.get('setup')==[],'Use normal Chill Mode without hidden setup')
 branches=e['branches'];count=len(branches);checks=data.get('expected',{});reveal=data.get('presentation',{}).get('choiceReveal',{})
 require(checks.get('initialStatus')=='dilemma','Intermediate stories must assert Dilemma')
 require(checks.get('boards')==count+1 and checks.get('validSlots')==list(range(count+1)),'Every exhaustive trial needs a separate valid copied board')
 require(checks.get('slotFills')==[[slot,i//9,i%9,d] for slot,b in enumerate(branches,1) for i,d in b],'Story fills must match its proved trials')
 require(checks.get('overlays')==[[slot,0] for slot in range(1,count+1)],'Every trial must overlay the original')
 require(checks.get('notes')==[[i//9,i%9,d,False] for i,d in e['targets']],'Remove exactly the common proved targets')
 cells=sorted({i for b in branches for i,d in b})
 require(checks.get('fills')==[[i//9,i%9,0] for i in cells],'The original board must remain unfilled')
 require(reveal.get('frames')==e['frames'] and reveal.get('labels')==e['labels'] and checks.get('revealFrameCount')==len(e['frames']) and checks.get('revealLabelCount')==len(e['labels']),'Reveal the complete native named-pattern premises')
 taps=[];downs=[];moves=[];ready=[]
 cell=lambda i:{'part':'cell','cell':[i//9,i%9]}
 slot=lambda n:{'part':'slot','slot':n}
 for k,b in enumerate(branches):
  if k:taps.append((slot(1),1))
  taps.append((slot(k+2),1));downs.append(cell(b[0][0]));ready.append(b[0][1])
  for i,d in b[1:]:taps.append((cell(i),2))
 taps.append((slot(1),1))
 downs.extend(slot(n) for n in range(2,count+2));downs.extend(cell(i) for i,d in e['targets'])
 frames=data.get('frames',[])
 require(all(f['do'] in {'hover','tap','depart','hide','down','move','ready','up'} for f in frames),'Unsupported extra tutorial action')
 require(reveal.get('start')==500,'Reveal the starting premises before exploring')
 require([(f.get('at'),f.get('count',1)) for f in frames if f['do']=='tap']==taps,'Copy by empty-slot taps and center-double-tap only forced moves')
 require([f.get('at') for f in frames if f['do']=='down']==downs,'One founding wheel gesture per trial, then real overlays and note strikes')
 require([f.get('digit') for f in frames if f['do']=='ready']==ready,'Wheel choices must match the exhaustive founding guesses')
 moving=[f.get('at') for f in frames if f['do']=='move'];require(len(moving)==count*2+len(e['targets']),'No extra gesture moves')
 for target,b in zip(moving[:count],branches):
  i,d=b[0];r,c=divmod(d-1,3);require(target=={**cell(i),'offset':[1.2*(c-1),1.2*(r-1)]},'Founding guess must use its own directional wheel choice')
 require(moving[count:count*2]==[slot(1)]*count,'Overlay every copy onto its original')
 import math
 for target,(i,d) in zip(moving[count*2:],e['targets']):
  r,c=divmod(d-1,3);dx,dy=c-1,r-1;scale=1.617/(math.sqrt(2) if dx and dy else 1)
  require(target=={**cell(i),'offset':[scale*dx,scale*dy]},'Remove proved notes with the correct quick wheel direction')
 require(len([f for f in frames if f['do']=='up'])==count*2+len(e['targets']),'Every drag must release')
 expected_order=[]
 for k,b in enumerate(branches):
  if k:expected_order.append('tap')
  expected_order.extend(['tap','down','move','ready','up'])
  expected_order.extend(['tap']*(len(b)-1))
 expected_order.append('tap')
 expected_order.extend(['down','move','up']*(count+len(e['targets'])))
 require([f['do'] for f in frames if f['do'] in {'tap','down','move','ready','up'}]==expected_order,'Execute each copy, guess, forced fill and released overlay in order')
 previous=-1
 for n,f in enumerate(frames):
  t=f.get('time');require(type(t) is int and t>previous,'Tutorial actions must have strictly increasing execution times');previous=t
  duration=f.get('ms',0);require(type(duration) is int and duration>=0,'Invalid gesture movement duration')
  if n+1<len(frames):require(t+duration<=frames[n+1].get('time',-1),'Finish each movement before the following action or release')
 require(type(data['presentation'].get('duration')) is int and data['presentation']['duration']>=previous+frames[-1].get('ms',0),'Tutorial must finish its last action')

 require(all(f.get('inputDelay')==440 for f in [x for x in frames if x['do']=='down'][count*2:]),'Strike notes quickly without a held wheel popup')
