// Shared API client. The same /api/* routes are served by web.py (local LAN, via tinytuya)
// and by the Netlify Function (Tuya cloud). Both may require a PIN.
const Bulb = (() => {
  const KEY = 'bulb-pin';
  const getPin = () => { try { return localStorage.getItem(KEY) || ''; } catch (e) { return ''; } };
  const setPin = p => { try { localStorage.setItem(KEY, p); } catch (e) {} };
  let memPin = getPin();

  async function request(action, body, askPin = true) {
    const opts = { method: body === undefined ? 'GET' : 'POST',
                   headers: { 'Content-Type': 'application/json', 'X-Bulb-Pin': memPin } };
    if (body !== undefined) opts.body = JSON.stringify(body);
    const r = await fetch('/api/' + action, opts);
    if (r.status === 401 && askPin) {
      const p = prompt('Enter your bulb PIN');
      if (p !== null) { memPin = p; setPin(p); return request(action, body, false); }
    }
    return r.json();
  }
  return { request };
})();
