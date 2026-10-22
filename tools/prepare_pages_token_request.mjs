import fs from 'node:fs/promises';
import { createECDH } from 'node:crypto';

// This prepares a public-key request for the connected Cloudflare tool. Only the
// project-scoped upload JWT is encrypted; account credentials never enter here.
const privateDirectory = new URL('../../private/', import.meta.url);
await fs.mkdir(privateDirectory, { recursive: true, mode: 0o700 });
const keyFile = new URL('pages-upload-transport.key', privateDirectory);
const local = createECDH('prime256v1');
try { local.setPrivateKey(await fs.readFile(keyFile)); }
catch (error) {
  if (error.code !== 'ENOENT') throw error;
  local.generateKeys();
  await fs.writeFile(keyFile, local.getPrivateKey(), { mode: 0o600, flag: 'wx' });
}
const publicKey = local.getPublicKey().toString('base64');
const code = `async () => {
  const token = await cloudflare.request({method:'GET',path:'/accounts/'+accountId+'/pages/projects/sudoku-joypace/upload-token'});
  const recipient = await crypto.subtle.importKey('raw',Uint8Array.from(atob(${JSON.stringify(publicKey)}),c=>c.charCodeAt(0)),{name:'ECDH',namedCurve:'P-256'},false,[]);
  const sender = await crypto.subtle.generateKey({name:'ECDH',namedCurve:'P-256'},true,['deriveKey']);
  const key = await crypto.subtle.deriveKey({name:'ECDH',public:recipient},sender.privateKey,{name:'AES-GCM',length:256},false,['encrypt']);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await crypto.subtle.encrypt({name:'AES-GCM',iv},key,new TextEncoder().encode(token.result.jwt));
  const raw = await crypto.subtle.exportKey('raw',sender.publicKey);
  const b64 = value => btoa(String.fromCharCode(...new Uint8Array(value)));
  return {project:'sudoku-joypace',sender:b64(raw),iv:b64(iv),ciphertext:b64(ciphertext)};
}`;
await fs.writeFile(new URL('pages-upload-token-request.js', privateDirectory), code + '\n', { mode: 0o600 });
console.log('Prepared project-only token request; public key only, no bearer credential output.');
