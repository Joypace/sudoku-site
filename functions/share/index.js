// Keep Safari's Open in App banner bound to this exact puzzle URL.
export async function onRequest({request, env}) {
  const asset = await env.ASSETS.fetch(request);
  if (asset.status !== 200 || !asset.headers.get('content-type')?.includes('text/html')) return asset;
  const headers = new Headers(asset.headers);
  headers.set('Cache-Control', 'no-store');
  headers.delete('Content-Length');
  headers.delete('ETag');
  if (request.method === 'HEAD') return new Response(null, {status: 200, headers});
  const html = await asset.text();
  const marker = 'app-argument=https://sudoku.joypace.com/share/';
  if (html.split(marker).length !== 2) throw new Error('Share banner template is missing or duplicated');
  const url = request.url.replace(/[&"<>']/g, char => ({'&':'&amp;','"':'&quot;','<':'&lt;','>':'&gt;',"'":'&#39;'}[char]));
  return new Response(html.replace(marker, 'app-argument=' + url), {status: 200, headers});
}
