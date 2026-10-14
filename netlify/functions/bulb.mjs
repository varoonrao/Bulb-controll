// Netlify Function: controls the bulb through the Tuya Cloud OpenAPI.
// Serves the same /api/* routes as web.py, so public/ works unchanged on either backend.
//
// Environment variables (Netlify → Site configuration → Environment variables):
//   TUYA_ACCESS_ID      Access ID from your Tuya IoT cloud project
//   TUYA_ACCESS_SECRET  Access Secret from the same project
//   TUYA_DEVICE_ID      bulb's device / virtual ID
//   TUYA_REGION         in | eu | us | cn  (data centre of your Smart Life account, default "in")
//   APP_PIN             required: PIN the web app must send (this URL is public!)
//   BULB_NAME           optional display name
import crypto from 'node:crypto';

const HOSTS = { in: 'openapi.tuyain.com', eu: 'openapi.tuyaeu.com', us: 'openapi.tuyaus.com', cn: 'openapi.tuyacn.com' };
const DEFAULT_DEVICE_ID = 'd756e7d3b52f4847ba0xdi';

// Warm-instance caches
let token = null;            // { value, expires }
let codes = null;            // Set of DP codes the bulb reports, to tell v1 from v2 firmware

const env = k => (typeof Netlify !== 'undefined' ? Netlify.env.get(k) : process.env[k]);
const cfg = () => ({
  id: env('TUYA_ACCESS_ID'),
  secret: env('TUYA_ACCESS_SECRET'),
  device: env('TUYA_DEVICE_ID') || DEFAULT_DEVICE_ID,
  host: HOSTS[(env('TUYA_REGION') || 'in').toLowerCase()] || env('TUYA_REGION'),
});

const sha256 = s => crypto.createHash('sha256').update(s).digest('hex');
const hmac = (key, s) => crypto.createHmac('sha256', key).update(s).digest('hex').toUpperCase();

// Tuya "new" signature: client_id [+ access_token] + t + nonce + stringToSign
// stringToSign = METHOD \n sha256(body) \n (no signed headers) \n path?sortedQuery
export function sign({ id, secret, accessToken = '', t, method, path, body = '' }) {
  const stringToSign = [method, sha256(body), '', path].join('\n');
  return hmac(secret, id + accessToken + t + stringToSign);
}

export async function tuya(method, path, bodyObj, { auth = true } = {}) {
  const c = cfg();
  if (!c.id || !c.secret) throw new HttpError(500, 'TUYA_ACCESS_ID / TUYA_ACCESS_SECRET are not set in Netlify');
  const accessToken = auth ? await getToken() : '';
  const body = bodyObj ? JSON.stringify(bodyObj) : '';
  const t = String(Date.now());
  const headers = {
    client_id: c.id, t, sign_method: 'HMAC-SHA256',
    sign: sign({ id: c.id, secret: c.secret, accessToken, t, method, path, body }),
    'Content-Type': 'application/json',
  };
  if (accessToken) headers.access_token = accessToken;
  const r = await fetch(`https://${c.host}${path}`, { method, headers, body: body || undefined });
  const j = await r.json();
  if (!j.success) {
    if (auth && (j.code === 1010 || j.code === 1011)) token = null;  // expired/invalid token
    throw new HttpError(502, `Tuya: ${j.msg} (code ${j.code})`);
  }
  return j.result;
}

async function getToken() {
  if (token && token.expires > Date.now()) return token.value;
  const r = await tuya('GET', '/v1.0/token?grant_type=1', null, { auth: false });
  token = { value: r.access_token, expires: Date.now() + (r.expire_time - 60) * 1000 };
  return token.value;
}

class HttpError extends Error { constructor(status, msg) { super(msg); this.status = status; } }

// ---------- bulb model ----------
const devPath = sub => `/v1.0/iot-03/devices/${cfg().device}/${sub}`;
const clamp = (v, lo = 0, hi = 100) => Math.max(lo, Math.min(hi, Math.round(Number(v))));
const num = v => { const n = Number(v); if (!Number.isFinite(n)) throw new HttpError(400, 'expected a number'); return n; };

async function status() {
  const list = await tuya('GET', devPath('status'));
  codes = new Set(list.map(x => x.code));
  const dps = Object.fromEntries(list.map(x => [x.code, x.value]));
  const sw = dps.switch_led ?? dps.led_switch;
  return { is_on: sw, switch: sw, mode: dps.work_mode,
           brightness: dps.bright_value_v2 ?? dps.bright_value,
           colourtemp: dps.temp_value_v2 ?? dps.temp_value,
           colour: dps.colour_data_v2 ?? dps.colour_data, dps };
}

async function isV2() {
  if (!codes) await status();
  return !codes.has('bright_value') || codes.has('bright_value_v2');
}

async function send(commands) {
  return tuya('POST', devPath('commands'), { commands });
}

async function white(bri, temp) {
  const v2 = await isV2();
  return send([
    { code: 'switch_led', value: true },
    { code: 'work_mode', value: 'white' },
    v2 ? { code: 'bright_value_v2', value: 10 + clamp(bri) * 9.9 | 0 } : { code: 'bright_value', value: 25 + clamp(bri) * 2.3 | 0 },
    v2 ? { code: 'temp_value_v2', value: clamp(temp) * 10 } : { code: 'temp_value', value: clamp(temp) * 2.55 | 0 },
  ]);
}

async function hsv(h, s = 100, v = 100) {
  const v2 = await isV2();
  const hue = ((Math.round(num(h)) % 360) + 360) % 360;
  const val = Math.max(1, clamp(v));
  const colour = v2 ? { h: hue, s: clamp(s) * 10, v: val * 10 }
                    : { h: hue, s: clamp(s) * 2.55 | 0, v: val * 2.55 | 0 };
  return send([
    { code: 'switch_led', value: true },
    { code: 'work_mode', value: 'colour' },
    { code: v2 ? 'colour_data_v2' : 'colour_data', value: colour },
  ]);
}

function hexToHsv(hex) {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex || '');
  if (!m) throw new HttpError(400, 'Colour must look like #ff8800');
  const [r, g, b] = [0, 2, 4].map(i => parseInt(m[1].slice(i, i + 2), 16) / 255);
  const max = Math.max(r, g, b), d = max - Math.min(r, g, b);
  let h = 0;
  if (d) h = max === r ? ((g - b) / d) % 6 : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return [h * 60, max ? d / max * 100 : 0, max * 100];
}

// Cloud "scenes" are vendor specific, so map the app's scene buttons to white presets
const SCENES = { night: [5, 0], read: [100, 50], work: [100, 100], leisure: [60, 20] };

const ACTIONS = {
  info: async () => null,
  status,
  on: () => send([{ code: 'switch_led', value: true }]),
  off: () => send([{ code: 'switch_led', value: false }]),
  toggle: async () => send([{ code: 'switch_led', value: !(await status()).is_on }]),
  brightness: async d => {
    const v2 = await isV2();
    return send([v2 ? { code: 'bright_value_v2', value: 10 + clamp(num(d.value)) * 9.9 | 0 }
                    : { code: 'bright_value', value: 25 + clamp(num(d.value)) * 2.3 | 0 }]);
  },
  temp: d => white(100, num(d.value)),
  white: d => white(d.brightness ?? 100, d.temp ?? 50),
  color: d => hsv(...hexToHsv(d.hex)),
  hsv: d => hsv(d.h, d.s ?? 100, d.v ?? 100),
  scene: d => {
    const preset = SCENES[String(d.name).toLowerCase()];
    if (!preset) throw new HttpError(400, `unknown scene ${d.name}`);
    return white(...preset);
  },
};

const json = (status, obj) => new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });

function pinOk(req) {
  const pin = env('APP_PIN');
  if (!pin) return false;   // refuse to run open on the public internet
  const got = Buffer.from(req.headers.get('x-bulb-pin') || '');
  const want = Buffer.from(pin);
  return got.length === want.length && crypto.timingSafeEqual(got, want);
}

export default async (req) => {
  const action = new URL(req.url).pathname.replace(/^\/api\//, '').replace(/\/$/, '');
  if (!env('APP_PIN')) return json(500, { ok: false, error: 'Set APP_PIN in Netlify environment variables first' });
  if (!pinOk(req)) return json(401, { ok: false, error: 'PIN required' });
  const fn = ACTIONS[action];
  if (!fn) return json(404, { ok: false, error: `unknown action ${action}` });
  const isRead = action === 'info' || action === 'status';
  if (!isRead && req.method !== 'POST') return json(405, { ok: false, error: 'use POST' });
  try {
    const data = req.method === 'POST' ? await req.json().catch(() => ({})) : {};
    const result = await fn(data);
    return json(200, { ok: true, result, backend: 'cloud', name: env('BULB_NAME') || 'Room Bulb' });
  } catch (e) {
    return json(e.status || 500, { ok: false, error: e.message });
  }
};

export const config = { path: '/api/*' };
