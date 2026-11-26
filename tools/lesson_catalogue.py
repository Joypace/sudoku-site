"""Level navigation and the HoDoKu syllabus; publication comes from the manifest."""
import html,re
from urllib.parse import urlparse
LEVELS=('basic','intermediate','advanced','expert')
def require(ok,why):
 if not ok:raise ValueError(why)
def validate_curriculum(c,manifest):
 require(c.get('schema')==1 and c.get('source')=='https://hodoku.sourceforge.net/en/techniques.php','Invalid curriculum source/schema')
 levels=c.get('levels',[]);require([x.get('id') for x in levels]==list(LEVELS),'Curriculum needs the four ordered learning levels')
 for x in levels:require(type(x.get('title')) is str and x['title'] and type(x.get('description')) is str and x['description'],'Missing level text')
 families=c.get('families',[]);ids=[x.get('id') for x in families];require(len(ids)==len(set(ids)) and all(type(v) is str and re.fullmatch('[a-z][a-z0-9-]+',v) for v in ids),'Invalid curriculum families')
 require(all(type(x.get('title')) is str and x['title'] for x in families),'Missing family title')
 topics=c.get('techniques',[]);slugs=[]
 for x in topics:
  slug=x.get('slug');require(type(slug) is str and re.fullmatch('[a-z][a-z0-9-]+',slug) and slug not in {'index','learn','manifest','curriculum'},'Invalid curriculum technique slug');slugs.append(slug)
  require(x.get('level') in LEVELS and x.get('family') in ids,'Unknown technique level/family')
  require(type(x.get('title')) is str and x['title'] and type(x.get('sectionHeading')) is str and x['sectionHeading'],'Missing technique title/source heading')
  u=urlparse(x.get('sourceURL',''));require(u.scheme=='https' and u.netloc=='hodoku.sourceforge.net' and re.fullmatch('/en/tech_[a-z]+[.]php',u.path) and not u.query and (not u.fragment or re.fullmatch('[A-Za-z0-9_-]+',u.fragment)),'Unexpected technique reference URL')
 require(slugs and len(slugs)==len(set(slugs)),'Duplicate/empty curriculum')
 require({x['slug'] for x in manifest['lessons']}<=set(slugs),'Published lesson missing from curriculum')
 return {x['slug']:x for x in topics}
def body(c,manifest):
 topics=validate_curriculum(c,manifest);published={x['slug']:x for x in manifest['lessons']};families={x['id']:x['title'] for x in c['families']};esc=lambda x:html.escape(str(x),quote=True)
 nav=[];sections=[]
 for n,level in enumerate(c['levels'],1):
  key=level['id'];ready=[x for x in manifest['lessons'] if topics[x['slug']]['level']==key];pending=[x for x in c['techniques'] if x['level']==key and x['slug'] not in published]
  nav.append(f'<a href="#{key}">{esc(level["title"])} <span>{len(ready)}</span></a>');cards=[]
  for x in ready:
   t=topics[x['slug']];cards.append(f'<a class="lesson-card" href="/learn/{esc(x["slug"])}/"><span class="lesson-family">{esc(families[t["family"]])}</span><h3>{esc(x["title"])}</h3><p>{esc(x["description"])}</p><span class="lesson-card-foot">{len(x["examples"])} animated examples <span aria-hidden="true">↗</span></span></a>')
  roadmap=''
  if pending:roadmap='<details class="lesson-roadmap"><summary>'+str(len(pending))+' more techniques in preparation</summary><ul>'+''.join(f'<li><span>{esc(x["title"])}</span><small>{esc(families[x["family"]])}</small></li>' for x in pending)+'</ul></details>'
  sections.append(f'<section class="lesson-level" id="{key}" aria-labelledby="{key}-heading"><header class="lesson-level-heading"><span class="level-number" aria-hidden="true">{n:02}</span><div><h2 id="{key}-heading">{esc(level["title"])}</h2><p>{esc(level["description"])}</p></div><span class="level-count">{len(ready)} lessons</span></header>'+('<div class="lesson-list">'+''.join(cards)+'</div>' if cards else '<p class="learn-note">Lessons for this level are being prepared with verified examples and real App animations.</p>')+roadmap+'</section>')
 return '<main id="main" class="wrap learn-page"><p class="learn-kicker">Learn by exploring</p><h1>Find your next step.</h1><p class="learn-lede">Start with the basics or explore a new technique. Watch real App animations, compare copied boards and try the same puzzles yourself.</p><nav class="level-nav" aria-label="Lesson levels">'+''.join(nav)+'</nav>'+''.join(sections)+'<p class="curriculum-source">The syllabus follows <a href="https://hodoku.sourceforge.net/en/techniques.php">HoDoKu’s technique catalogue</a>. Learning levels are our guide to progression. Techniques marked “in preparation” will become playable lessons after their examples are verified.</p></main>'
