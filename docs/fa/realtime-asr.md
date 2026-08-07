<div dir="rtl">

# تایپ صوتی همزمان (ASR)

صوت را روی یک WebSocket استریم کنید و متن را هم‌زمان با صحبت گوینده دریافت نمایید. مناسب برای دستیارهای صوتی، زیرنویس زنده، دیکته، مراکز تماس و هر رابطی که نمی‌تواند تا پایان جمله منتظر بماند.

**آدرس:** `wss://iotype.com/socket/realtime`

**اسپک:** [`spec/asyncapi.yaml`](../../spec/asyncapi.yaml)

## چرخه‌ی جلسه

</div>

```
۱. باز کردن WebSocket
۲. ارسال پیام Initialize (JSON)    ← باید اولین پیام باشد؛ پیش از آن هیچ صوتی نفرستید
۳. اعتبارسنجی سرور و انتخاب مدل
۴. استریم صوت به‌صورت فریم باینری  ← پیوسته و در بسته‌های کوچک
۵. دریافت { type: "partial" }      ← حین صحبت، قابل تغییر
۶. دریافت { type: "final" }        ← در هر مکث، نهایی
۷. تکرار مراحل ۴ تا ۶ تا پایان جلسه
۸. بستن اتصال
```

<div dir="rtl">

## ۱. پیام Initialize

اولین پیام روی سوکت. هیچ چیز نباید پیش از آن ارسال شود.

</div>

```json
{
  "config": {
    "model": "io-fa",
    "type": "flash_token",
    "token": "YOUR_TOKEN"
  }
}
```

<div dir="rtl">

> **هر سه پارامتر داخل `config` قرار می‌گیرند.** ارسال آن‌ها در سطح بالا خطای
> پروتکل است. نسخه‌های قبلی مستندات رسمی این پارامترها را بدون `config` نشان
> می‌دادند — اگر کد قدیمی دارید، همین خط را باید تغییر دهید.

| پارامتر | نوع | الزامی | مقادیر |
| --- | --- | --- | --- |
| `config.model` | string | بله | `io-fa` فارسی · `io-en` انگلیسی · `io-ar` عربی |
| `config.type` | string | بله | `access_token` · `flash_token` |
| `config.token` | string | بله | مقدار اعتبارنامه |

مقدار `model` باید با زبان گفتار هم‌خوان باشد. ناهماهنگی، دقت را به‌شدت کاهش می‌دهد.

در هر کلاینتی که کنترلش با شما نیست — مرورگر، اندروید، iOS، دسکتاپ — از `flash_token` استفاده کنید. `access_token` فقط برای ارتباط سرور به سرور. توضیح بیشتر در [احراز هویت](authentication.md).

## ۲. فرمت صوت

صوت را به‌صورت **فریم باینری خام** بفرستید. نه Base64، نه داخل JSON.

| ویژگی | مقدار |
| --- | --- |
| Encoding | PCM Linear 16-bit |
| کانال | Mono (تک‌کاناله) |
| ترتیب بایت | Little Endian |
| نرخ نمونه‌برداری | ۱۶۰۰۰ هرتز (توصیه‌شده) |

دو نکته که به‌سادگی اشتباه می‌شوند:

- **نرخ نمونه‌برداری اعلام‌شده باید دقیقاً با داده‌ی ارسالی یکسان باشد.** ناهماهنگی در resampling یکی از دلایل رایج خروجی مخدوش است.
- **فقط تک‌کاناله.** ورودی استریو کیفیت تشخیص را پایین می‌آورد؛ پیش از ارسال آن را به mono تبدیل کنید.

### اندازه‌ی بسته

پیوسته و در بسته‌های کوچک بفرستید — حدود ۲۰ تا ۱۰۰ میلی‌ثانیه صوت در هر فریم. در ۱۶ کیلوهرتز تک‌کاناله ۱۶ بیتی، یعنی ۶۴۰ تا ۳۲۰۰ بایت در هر فریم.

بسته‌های بزرگ و کم‌تعداد، هم تأخیر را زیاد می‌کنند و هم دقت را پایین می‌آورند. چند ثانیه صوت را بافر نکنید تا یک‌جا بفرستید.

## ۳. پاسخ‌ها

سرور روی همان سوکت، پیام JSON می‌فرستد.

### Partial

</div>

```json
{ "type": "partial", "text": "سلام حال" }
```

<div dir="rtl">

متن موقت که حین گفتار تولید می‌شود. ممکن است چندین بار برای یک بخش ارسال شود و **ممکن است اصلاح شود**. آن را در رابط کاربری نمایش دهید تا کاربر بازخورد لحظه‌ای ببیند، اما هرگز ذخیره‌اش نکنید.

### Final

</div>

```json
{ "type": "final", "text": "سلام حال شما چطور است؟" }
```

<div dir="rtl">

پس از مکث گوینده یا پایان یک عبارت ارسال می‌شود. دیگر تغییر نخواهد کرد. این را ذخیره کنید.

هر جلسه چندین Final تولید می‌کند و پس از هر کدام، تشخیص ادامه پیدا می‌کند.

### نمایش صحیح

دو بافر نگه دارید:

</div>

```js
let committed = "";      // اتصال همه‌ی finalها
let current   = "";      // آخرین partial

// در دریافت پیام
if (msg.type === "partial") current = msg.text;
if (msg.type === "final")  { committed += msg.text + " "; current = ""; }

render(committed + current);
```

<div dir="rtl">

اگر partialها را مستقیماً به متن اضافه کنید، خروجی تکراری و مخدوش می‌شود. این رایج‌ترین باگ در پیاده‌سازی ASR است.

## نمونه‌ی مرورگر

</div>

```js
// Flash Token از سرور شما می‌آید — سروری که Access Token را نگه می‌دارد.
const { token } = await fetch("/api/iotype-flash-token").then(r => r.json());

const ws = new WebSocket("wss://iotype.com/socket/realtime");
ws.binaryType = "arraybuffer";

let committed = "", current = "";

ws.onopen = async () => {
  ws.send(JSON.stringify({ config: { model: "io-fa", type: "flash_token", token } }));

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const ctx = new AudioContext({ sampleRate: 16000 });
  const src = ctx.createMediaStreamSource(stream);
  const node = ctx.createScriptProcessor(2048, 1, 1);

  node.onaudioprocess = e => {
    if (ws.readyState !== WebSocket.OPEN) return;
    const f32 = e.inputBuffer.getChannelData(0);
    const i16 = new Int16Array(f32.length);
    for (let i = 0; i < f32.length; i++) {
      const s = Math.max(-1, Math.min(1, f32[i]));
      i16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;   // float32 به PCM16
    }
    ws.send(i16.buffer);                           // باینری خام
  };

  src.connect(node);
  node.connect(ctx.destination);
};

ws.onmessage = e => {
  const msg = JSON.parse(e.data);
  if (msg.type === "partial") current = msg.text;
  if (msg.type === "final") { committed += msg.text + " "; current = ""; }
  document.getElementById("out").textContent = committed + current;
};
```

<div dir="rtl">

> `ScriptProcessorNode` منسوخ شده است. در محیط عملیاتی، تبدیل float32 به PCM16 را داخل یک `AudioWorklet` ببرید تا روی نخ اصلی اجرا نشود.

## نمونه‌ی سمت سرور

کلاینت‌های آماده در SDKها موجودند:

- [پایتون](../../sdk/python/) — `Iotype.realtime()`
- [جاوااسکریپت](../../sdk/javascript/) — `Iotype.realtime()`
- [Go](../../sdk/go/) — `Client.Realtime()`
- [PHP](../../sdk/php/) — `Client::realtime()`

## عیب‌یابی

| نشانه | علت محتمل |
| --- | --- |
| سوکت بلافاصله بعد از باز شدن بسته می‌شود | پیام Initialize ارسال نشده، ناقص است، یا پیش از آن صوت فرستاده شده |
| متن خالی یا بی‌معنا | ناهماهنگی نرخ نمونه‌برداری، صوت استریو، endian اشتباه، یا داده‌ی Base64 |
| زبان خروجی اشتباه | مقدار `model` با زبان گفتار هم‌خوان نیست |
| تأخیر زیاد | بسته‌ها بزرگ‌اند یا صوت پیش از ارسال بافر شده |
| متن تکراری در رابط کاربری | partialها اضافه شده‌اند به‌جای آنکه جایگزین شوند |

</div>

<div dir="rtl">

---

## همچنین ببینید

- [وب سرویس تایپ صوتی همزمان](https://iotype.com/api-service/speech-to-text) — مستندات رسمی آی او تایپ
- [تبدیل فایل صوتی به متن](transcription.md) اگر فایل ضبط‌شده دارید نه استریم زنده
- [احراز هویت](authentication.md) برای فرآیند Flash Token · [خطاها](errors.md)

</div>
