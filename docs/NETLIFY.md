# Deploy the gyro app to Netlify

On Netlify the app runs on the internet, not on your home Wi-Fi, so it controls the bulb through
the **Tuya cloud API** instead of the local key:

```
 Phone (Chrome, https) ──▶ Netlify: public/ + netlify/functions/bulb.mjs ──▶ Tuya cloud (India) ──▶ 💡
```

Upsides compared with Termux: no server on your phone, it works from anywhere (even off Wi-Fi), and
it's HTTPS so the gyro works in any browser. Downsides: about 0.3–0.8 s of lag per update, and the
free Tuya plan has a monthly API-call quota. In cloud mode the app sends at most ~1–2 updates/s, and
only when the colour changes noticeably.

## 1. Tuya cloud project (one-time)

Same steps as [SETUP.md](SETUP.md), sections 1–2:

1. Pair the bulb with the **Smart Life** app.
2. Create a cloud project at <https://platform.tuya.com> with data centre **India**.
3. **Devices → Link App Account** and scan the QR code with Smart Life. Your bulb
   (`d756e7d3b52f4847ba0xdi`) should appear in the device list.
4. **Service API**: make sure **IoT Core** is subscribed.
5. Copy the **Access ID** and **Access Secret** from *Overview*.

## 2. Create the Netlify site

1. Netlify → **Add new project → Import an existing project → GitHub**.
2. Pick **varoonrao/Bulb-controll**.
3. Branch to deploy: `main`, or `claude/havel-smart-bulb-control-024lsd` if it isn't merged yet.
4. Leave build command empty. `netlify.toml` already sets publish dir `public` and functions dir
   `netlify/functions`.
5. Click **Deploy**.

## 3. Environment variables

Netlify → your site → **Site configuration → Environment variables → Add a variable**:

| Key | Value |
|---|---|
| `TUYA_ACCESS_ID` | Access ID from the Tuya project |
| `TUYA_ACCESS_SECRET` | Access Secret from the Tuya project (mark it **secret**) |
| `TUYA_DEVICE_ID` | `d756e7d3b52f4847ba0xdi` (also the default if unset) |
| `TUYA_REGION` | `in` (India; or `eu`, `us`, `cn` to match your Smart Life account) |
| `APP_PIN` | a PIN of your choice. **Required**: the site URL is public, and without a PIN anyone could control your light |
| `BULB_NAME` | optional, e.g. `Bedroom` |

Then **Deploys → Trigger deploy → Deploy project** so the function picks up the variables.

## 4. Use it

Open `https://<your-site>.netlify.app` on your Android phone in Chrome and tap **Start gyro**.
Enter your PIN once; the browser remembers it. Use Chrome menu → **Add to Home screen** to get
an app icon. `/remote` is the slider remote.

## Troubleshooting

The red dot / hint text shows the Tuya error message:

| Error | Fix |
|---|---|
| `TUYA_ACCESS_ID ... not set` / `Set APP_PIN` | Add the env vars, then redeploy |
| `sign invalid (code 1004)` | Access ID/Secret mistyped, or extra spaces |
| `No permissions. Your subscription to cloud development plan has expired` (28841002) | Renew/extend the free IoT Core trial in the Tuya console |
| `permission deny (code 1106)` | The bulb isn't linked to this cloud project (step 1.3), or wrong `TUYA_REGION` |
| `device is offline` | The bulb is switched off at the wall or lost Wi-Fi |
| `command or value not support` | Your bulb uses different DP codes. Open `/api/status` (with the `X-Bulb-Pin` header) to see them, and open an issue |
