import assert from 'node:assert/strict';

const terminal = child => child.exitCode !== null || child.signalCode !== null;
async function waitForExit(child, milliseconds) {
  if (terminal(child)) return;
  await new Promise(resolve => {
    const onExit = () => { clearTimeout(timer); resolve(); };
    const timer = setTimeout(() => { child.removeListener('exit', onExit); resolve(); }, milliseconds);
    child.once('exit', onExit);
  });
}

export async function closeOwnedBrowser(browser) {
  let forced = false;
  if (!terminal(browser)) {
    browser.kill('SIGTERM');
    await waitForExit(browser, 10000);
  }
  if (!terminal(browser)) {
    forced = true;
    browser.kill('SIGKILL');
    await waitForExit(browser, 5000);
  }
  assert(terminal(browser), 'Owned browser not terminal');
  return {pid: browser.pid, exitCode: browser.exitCode, signalCode: browser.signalCode, forced};
}
