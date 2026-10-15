import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {spawn} from 'node:child_process';
import assert from 'node:assert/strict';
const url=process.argv[2]||'http://127.0.0.1:8090/';
const profile=await fs.mkdtemp(path.join(os.tmpdir(),'homepage-svg-browser-'));
const browser=spawn(process.env.CHROME_BIN||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',[
 '--headless=new','--no-first-run','--no-default-browser-check','--disable-background-networking',`--user-data-dir=${profile}`,'--remote-debugging-port=0','about:blank'],{stdio:'ignore'});
let socket;
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
try{
 let port;for(let i=0;i<100;i++){try{port=Number((await fs.readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0]);break}catch{await wait(100)}}
 assert(port);
 const pages=await(await fetch(`http://127.0.0.1:${port}/json`)).json();
 socket=new WebSocket(pages.find(page=>page.type==='page').webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject});
 let serial=0;const pending=new Map(),requests=[],exceptions=[];
 socket.onmessage=event=>{const m=JSON.parse(event.data);
  if(m.method==='Network.requestWillBeSent')requests.push(m.params.request.url);
  if(m.method==='Runtime.exceptionThrown')exceptions.push(m.params.exceptionDetails.text);
  if(m.id){const p=pending.get(m.id);pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result)}
 };
 const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial,timer=setTimeout(()=>reject(Error(method+' timeout')),20000);pending.set(id,{resolve,reject,timer});socket.send(JSON.stringify({id,method,params}))});
 const read=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value};
 const until=async(expression,message)=>{for(let i=0;i<200;i++){if(await read(expression))return;await wait(25)}throw Error(message)};
 await call('Page.enable');await call('Runtime.enable');await call('Network.enable');
 await call('Emulation.setDeviceMetricsOverride',{width:1100,height:850,deviceScaleFactor:1,mobile:false});
 await call('Page.navigate',{url});
 await until(`!!document.querySelector('.tip-animation')`,'Homepage missing');
 await read(`document.querySelector('.tip-animation').scrollIntoView({block:'center',behavior:'instant'})`);
 const svg=`document.querySelector('.tip-animation object')?.contentDocument?.documentElement`;
 await until(`${svg}?.localName==='svg' && !${svg}.animationsPaused() && ${svg}.getCurrentTime()>0`,'Visible animation did not autoplay without a click');
 await read(`${svg}.setCurrentTime(Number(${svg}.dataset.duration)+.01)`);
 await until(`${svg}.animationsPaused()`,'End-of-animation reading pause missing');
 await wait(1000);
 assert(await read(`${svg}.animationsPaused()`),'Loop restarted before its reading pause');
 await until(`!${svg}.animationsPaused() && ${svg}.getCurrentTime()<1`,'Animation did not loop after the 1.5-second pause');
 await read(`scrollTo({top:0,behavior:'instant'})`);
 await until(`${svg}.animationsPaused()`,'Offscreen animation did not stop');
 await read(`document.querySelector('.tip-animation').scrollIntoView({block:'center',behavior:'instant'})`);
 await until(`!${svg}.animationsPaused()`,'Returning animation did not autoplay');
 for(const width of [834,390,320]){
  await call('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:false});
  assert.equal(await read('document.documentElement.scrollWidth'),width,'Horizontal overflow');
 }
 await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
 await call('Page.navigate',{url});
 await until(`!!document.querySelector('.tip-animation')`,'Reduced-motion homepage missing');
 await read(`document.querySelector('.tip-animation').scrollIntoView({block:'center',behavior:'instant'})`);await wait(300);
 assert.equal(await read(`document.querySelectorAll('.tip-vector').length`),0,'Reduced motion ignored');
 assert(!requests.some(value=>/\.wasm(?:\?|$)|flutter(?:_bootstrap)?\.js|main\.dart\.js/.test(value)),'Homepage downloaded a Flutter runtime');
 assert.equal(exceptions.length,0,JSON.stringify(exceptions));
 console.log('PASS: click-free visible autoplay, 1.5-second reading gap and repeat, offscreen stop, return autoplay, responsive widths, reduced motion; no Flutter web runtime');
}finally{socket?.close();browser.kill()}
