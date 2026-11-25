import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {spawn} from 'node:child_process';
import assert from 'node:assert/strict';
const url=process.argv[2];assert(url,'Supply the local lesson URL');
const output=path.resolve(process.argv[3]||os.tmpdir());await fs.mkdir(output,{recursive:true});
const profile=await fs.mkdtemp(path.join(os.tmpdir(),'lesson-qa-'));
const browser=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--no-first-run','--no-default-browser-check','--disable-background-networking',`--user-data-dir=${profile}`,'--remote-debugging-port=0','about:blank'],{stdio:'ignore'});
const wait=ms=>new Promise(r=>setTimeout(r,ms));let socket;
try{
 let port;for(let i=0;i<100;i++){try{port=Number((await fs.readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0]);break}catch{await wait(100)}}assert(port);
 const tabs=await(await fetch(`http://127.0.0.1:${port}/json`)).json();socket=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j});let serial=0;const pending=new Map(),errors=[];
 socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);if(m.id){const p=pending.get(m.id);pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result)}};
 const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial,timer=setTimeout(()=>reject(Error(method+' timeout')),20000);pending.set(id,{resolve,reject,timer});socket.send(JSON.stringify({id,method,params}))});
 const read=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value};
 const until=async(expression,label)=>{for(let i=0;i<200;i++){if(await read(expression))return;await wait(50)}throw Error(label)};
 await call('Page.enable');await call('Runtime.enable');await call('Emulation.setDeviceMetricsOverride',{width:1280,height:950,deviceScaleFactor:1,mobile:false});await call('Page.navigate',{url});await until('document.querySelectorAll("[data-example-animation]").length===3','Three examples missing');
 const responsive=[];
 for(const width of [320,390,834,1280]){
  await call('Emulation.setDeviceMetricsOverride',{width,height:950,deviceScaleFactor:1,mobile:false});await wait(80);const v=await read('({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,bodyFont:getComputedStyle(document.body).fontSize,links:[...document.querySelectorAll(".play-example")].map(a=>a.href)})');assert.equal(v.scrollWidth,width,'Horizontal page overflow '+width);assert.equal(v.links.length,3);responsive.push(v);
 }
 await read('document.querySelector("[data-example-animation]").scrollIntoView({block:"center",behavior:"instant"})');
 const svg='document.querySelector("[data-example-animation] object")?.contentDocument?.documentElement';
 await until(`${svg}?.localName==='svg' && !document.querySelector('[data-play]').disabled`,'First real SVG not ready');assert(await read(`${svg}.animationsPaused() && ${svg}.getCurrentTime()<.05`),'Unexpected autoplay');
 await read('document.querySelector("[data-play]").click()');await until(`${svg}.getCurrentTime()>.2 && !${svg}.animationsPaused()`,'Play did not advance');await read('document.querySelector("[data-play]").click()');assert(await read(`${svg}.animationsPaused()`));const paused=await read(`${svg}.getCurrentTime()`);await wait(150);assert(Math.abs(await read(`${svg}.getCurrentTime()`)-paused)<.06);
 const seekTime=await read('Number(document.querySelector(".animation-controls input").max)/2');assert(seekTime>0);
 await read(`const s=document.querySelector(".animation-controls input");s.value=${seekTime};s.dispatchEvent(new Event("input",{bubbles:true}))`);assert(Math.abs(await read(`${svg}.getCurrentTime()`)-seekTime)<.06,'Scrub did not seek');
 await read('document.querySelector("[data-replay]").click()');await until(`${svg}.getCurrentTime()<1 && !${svg}.animationsPaused()`,'Replay did not restart');await read('document.querySelector("[data-play]").click()');
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:950,deviceScaleFactor:1,mobile:false});await read('document.querySelector("[data-enlarge]").click()');assert(await read('document.querySelector(".animation-viewport").scrollWidth>=680'));assert.equal(await read('document.documentElement.scrollWidth'),390);await read('document.querySelector("[data-enlarge]").click()');
 await fs.writeFile(path.join(output,'lesson-390.png'),Buffer.from((await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false})).data,'base64'));
 await call('Emulation.setDeviceMetricsOverride',{width:1280,height:950,deviceScaleFactor:1,mobile:false});await fs.writeFile(path.join(output,'lesson-1280.png'),Buffer.from((await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false})).data,'base64'));
 await read('document.querySelector("[data-play]").click();scrollTo({top:document.documentElement.scrollHeight,behavior:"instant"})');assert(await read('document.querySelector("[data-example-animation]").getBoundingClientRect().bottom<0'),'Test fixture did not move the first animation offscreen');await until(`${svg}.animationsPaused()`,'Offscreen animation kept playing');
 await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});await call('Page.navigate',{url});await until('document.querySelector("[data-example-animation]")','Reduced motion page missing');await read('document.querySelector("[data-example-animation]").scrollIntoView({block:"center",behavior:"instant"})');await until(`${svg}?.localName==='svg'&&!document.querySelector('[data-play]').disabled`,'Reduced motion SVG missing');assert(await read(`${svg}.animationsPaused()&&${svg}.getCurrentTime()<.05`),'Reduced motion autoplay');assert.equal(errors.length,0,errors.join(';'));
 await fs.writeFile(path.join(output,'browser-check.local.json'),JSON.stringify({state:'PASS',responsive,checks:['three original examples','paused initial frame','play/pause','seek','replay','mobile enlarge contained','offscreen pause','reduced motion','noJSexceptions'],errors},null,2));console.log('PASS responsive320/390/834/1280, actualAppSVG play/pause/seek/replay/enlarge/offscreen/reduced-motion checks');
}finally{
 socket?.close();if(browser.exitCode===null){browser.kill();await Promise.race([new Promise(r=>browser.once('exit',r)),wait(3000)])}assert(browser.exitCode!==null||browser.signalCode!==null,'Owned browser not terminal');await fs.rm(profile,{recursive:true,force:true});
}
