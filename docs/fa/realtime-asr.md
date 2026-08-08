<div dir="rtl">

# تایپ صوتی همزمان (ASR)

صوت را روی یک WebSocket استریم کنید و متن را هم‌زمان با صحبت گوینده دریافت نمایید. مناسب برای دستیارهای صوتی، زیرنویس زنده، دیکته، مراکز تماس و هر رابطی که نمی‌تواند تا پایان جمله منتظر بماند.

**آدرس:** `wss://iotype.com/socket/realtime`

**اسپک:** [`spec/asyncapi.yaml`](../../spec/asyncapi.yaml) · **کلاینت کامل:** [`examples/browser-asr/`](../../examples/browser-asr/)

> تمام ساختارهای پیام در این صفحه از یک کلاینت واقعی گرفته شده که اجرا و تست شده است. هر جا این صفحه با توضیحات جای دیگر تفاوت داشت، این صفحه رفتار واقعی سرور است.

## چرخه‌ی جلسه

</div>

```
۱. باز کردن WebSocket
۲. ارسال  { "config": { ... } }                       ← باید اولین پیام باشد
۳. انتظار { "status": "authorized", "sample_rate": N } ← پیش از این هیچ صوتی نفرستید
۴. تبدیل نرخ صوت ضبط‌شده به N هرتز
۵. استریم صوت به‌صورت فریم باینری                       ← هر فریم ۲۰ میلی‌ثانیه
۶. دریافت { "partial": "..." }                        ← حین صحبت، قابل تغییر
۷. دریافت { "text": "..." }                           ← در هر مکث، نهایی
۸. ارسال  { "eof": 1 }                                ← تخلیه‌ی دیکودر
۹. چند ثانیه صبر، سپس بستن اتصال
```

<div dir="rtl">

دو مرحله همان‌هایی هستند که معمولاً نادیده گرفته می‌شوند و هر دو جلسه را خراب می‌کنند: **انتظار برای پاسخ در مرحله‌ی ۳** و **ارسال `eof` در مرحله‌ی ۸**.

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

> **هر سه پارامتر داخل `config` قرار می‌گیرند.** ارسال آن‌ها در سطح بالا خطای پروتکل است.

| پارامتر | نوع | الزامی | مقادیر |
| --- | --- | --- | --- |
| `config.model` | string | بله | `io-fa` فارسی · `io-en` انگلیسی · `io-ar` عربی |
| `config.type` | string | بله | `access_token` · `flash_token` |
| `config.token` | string | بله | مقدار اعتبارنامه |

مقدار `model` باید با زبان گفتار هم‌خوان باشد. ناهماهنگی، دقت را به‌شدت کاهش می‌دهد.

در هر کلاینتی که کنترلش با شما نیست — مرورگر، اندروید، iOS، دسکتاپ — از `flash_token` استفاده کنید. `access_token` فقط برای ارتباط سرور به سرور. توضیح بیشتر در [احراز هویت وب سرویس](authentication.md).

## ۲. انتظار برای پاسخ

سرور به handshake پاسخ می‌دهد. **تا رسیدن این پیام هیچ صوتی نفرستید.**

</div>

```json
{ "status": "authorized", "model": "io-fa", "sample_rate": 44100 }
```

<div dir="rtl">

در صورت شکست:

</div>

```json
{ "error": "unauthorized" }
```

<div dir="rtl">

…و سرور اتصال را می‌بندد.

| فیلد | معنی |
| --- | --- |
| `status` | مقدار `authorized` یعنی توکن پذیرفته شد |
| `model` | مدلی که سرور انتخاب کرد — بازتاب درخواست شما |
| `sample_rate` | **نرخی که باید صوت را با آن بفرستید** |

### `sample_rate` یک عدد ثابت نیست

مهم‌ترین نکته‌ی این صفحه همین است. سرور می‌گوید چه نرخی می‌خواهد و شما صوت را به همان نرخ تبدیل می‌کنید. هرگز عدد را hardcode نکنید — ممکن است یک نصب روی ۴۴۱۰۰ هرتز کار کند و دیگری روی ۱۶۰۰۰.

در مرورگر این اجتناب‌ناپذیر است: `AudioContext` نرخ خودش را از سیستم‌عامل می‌گیرد که معمولاً ۴۸۰۰۰ هرتز است. تقریباً همیشه باید تبدیل کنید.

</div>

```js
const resampler = new StreamingResampler(context.sampleRate, auth.sample_rate);
```

<div dir="rtl">

ناهماهنگی نرخ نمونه‌برداری هیچ خطایی تولید نمی‌کند. فقط متنی می‌دهد که یا کمی غلط است یا کاملاً بی‌معنا — گیج‌کننده‌ترین حالت خرابی در این API.

## ۳. فرمت صوت

صوت را به‌صورت **فریم باینری خام** بفرستید. نه Base64، نه داخل JSON.

| ویژگی | مقدار |
| --- | --- |
| Encoding | PCM Linear 16-bit |
| کانال | Mono (تک‌کاناله) |
| ترتیب بایت | Little Endian |
| نرخ نمونه‌برداری | همان مقدار `sample_rate` |

### اندازه‌ی فریم

هر فریم ۲۰ میلی‌ثانیه — یعنی `sample_rate / 50` نمونه:

</div>

```js
const size = Math.round(sampleRate / 50);
```

<div dir="rtl">

در ۴۴۱۰۰ هرتز یعنی ۸۸۲ نمونه یا ۱۷۶۴ بایت. فریم‌های بزرگ و کم‌تعداد تأخیر را زیاد و دقت را کم می‌کنند؛ بافر کردن چند ثانیه صوت و ارسال یک‌جا اشتباه است.

کال‌بک‌های صوتی مضربی از ۲۰ میلی‌ثانیه نمی‌رسند، پس یک صف نگه دارید و از آن برش بزنید:

</div>

```js
queue = concat(queue, newSamples);
while (queue.length >= size) {
  ws.send(float32ToPcm16(queue.slice(0, size)));
  queue = queue.slice(size);
}
```

<div dir="rtl">

## ۴. پاسخ‌ها

دو ساختار پیام که با **حضور کلید** از هم تشخیص داده می‌شوند — فیلدی به نام `type` وجود ندارد.

### Partial

</div>

```json
{ "partial": "سلام حال" }
```

<div dir="rtl">

متن موقت که حین گفتار تولید می‌شود. ممکن است چندین بار برای یک بخش ارسال شود و **ممکن است اصلاح شود**. آن را برای بازخورد لحظه‌ای نمایش دهید، اما هرگز ذخیره‌اش نکنید. رشته‌ی خالی یعنی فرضیه پاک شده است.

### Final

</div>

```json
{ "text": "سلام حال شما چطور است؟" }
```

<div dir="rtl">

پس از مکث گوینده یا پس از ارسال `eof` می‌آید. دیگر تغییر نمی‌کند. این را ذخیره کنید.

هر جلسه چندین final تولید می‌کند. مقدار `text` ممکن است رشته‌ی خالی باشد وقتی یک عبارت چیزی تولید نکرده — پیش از افزودن، بررسی کنید.

### نمایش صحیح

این دو را در دو جای جدا نگه دارید:

</div>

```js
if (typeof data.partial === "string") {
  currentPartial = data.partial;                    // جایگزین کن
}
if (typeof data.text === "string" && data.text.trim()) {
  transcript.push(data.text.trim());                // اضافه کن
  currentPartial = "";
}

render(transcript.join(" ") + " " + currentPartial);
```

<div dir="rtl">

اگر partialها را به متن اضافه کنید، خروجی تکراری و مخدوش می‌شود. این رایج‌ترین باگ در پیاده‌سازی ASR است.

## ۵. پایان جلسه

</div>

```js
ws.send(float32ToPcm16(queue));        // تخلیه‌ی صوت باقی‌مانده
ws.send(JSON.stringify({ eof: 1 }));   // درخواست اتمام از دیکودر
setTimeout(() => ws.close(), 3000);    // فرصت پاسخ دادن
```

<div dir="rtl">

بستن سوکت بلافاصله پس از آخرین فریم صوتی **آخرین جمله را از بین می‌برد**. پیام `{"eof":1}` به سرور می‌گوید دیکودر را تخلیه کند؛ آخرین پیام `text` کمی بعد می‌رسد.

## نمونه‌ی کامل

یک کلاینت مرورگری قابل اجرا در [`examples/browser-asr/`](../../examples/browser-asr/) قرار دارد — ضبط میکروفون، تبدیل نرخ، فریم‌بندی، نمایش و بستن اتصال، در حدود ۱۰۰ خط و بدون هیچ وابستگی.

</div>

```bash
cd examples/browser-asr && python3 -m http.server 8080
```

<div dir="rtl">

طرح کلی هسته‌ی کار:

</div>

```js
// Flash Token از سرور شما می‌آید — سروری که Access Token را نگه می‌دارد.
const { token } = await fetch("/api/iotype-flash-token").then(r => r.json());

const ws = new WebSocket("wss://iotype.com/socket/realtime");
ws.binaryType = "arraybuffer";

// ۱. handshake، ۲. انتظار برای پاسخ
const auth = await new Promise((resolve, reject) => {
  ws.onopen = () => ws.send(JSON.stringify({
    config: { model: "io-fa", type: "flash_token", token }
  }));
  ws.onmessage = e => {
    const d = JSON.parse(e.data);
    if (d.status === "authorized") resolve(d);
    if (d.error) reject(new Error(d.error));
  };
});

// ۳. تبدیل نرخ صوت به auth.sample_rate و ارسال فریم‌های باینری ۲۰ میلی‌ثانیه‌ای
// ۴. خواندن نتایج
ws.onmessage = e => {
  const d = JSON.parse(e.data);
  if (typeof d.partial === "string") showInterim(d.partial);
  if (typeof d.text === "string" && d.text.trim()) commit(d.text.trim());
};
```

<div dir="rtl">

## SDKها

هر کدام handshake کامل، قرارداد تبدیل نرخ و بستن با `eof` را پیاده کرده‌اند:

- [پایتون](../../sdk/python/) — `Iotype.realtime()`
- [جاوااسکریپت](../../sdk/javascript/) — `Iotype.realtime()`
- [Go](../../sdk/go/) — `Client.Realtime()`
- [PHP](../../sdk/php/) — `Client::realtime()`

## عیب‌یابی

| نشانه | علت محتمل |
| --- | --- |
| سوکت بلافاصله بعد از باز شدن بسته می‌شود | پیام `config` ارسال نشده یا ناقص است، یا صوت پیش از پاسخ `authorized` فرستاده شده |
| `{"error": "unauthorized"}` | توکن نامعتبر، انقضای Flash Token، یا اتمام اعتبار |
| متن خالی یا بی‌معنا | **نرخ نمونه‌برداری با `sample_rate` یکی نیست** — محتمل‌ترین علت. همچنین: صوت استریو، endian اشتباه، یا داده‌ی Base64 |
| آخرین جمله هرگز نمی‌رسد | سوکت بدون ارسال `{"eof":1}` بسته شده، یا خیلی زود بسته شده |
| زبان خروجی اشتباه | مقدار `model` با زبان گفتار هم‌خوان نیست |
| تأخیر زیاد | فریم‌ها بزرگ‌اند یا صوت پیش از ارسال بافر شده |
| متن تکراری در رابط کاربری | partialها اضافه شده‌اند به‌جای آنکه جایگزین شوند |

---

## همچنین ببینید

- [وب سرویس تایپ صوتی همزمان](https://iotype.com/api-service/speech-to-text) — مستندات رسمی آی او تایپ
- [نمونه‌ی کلاینت مرورگر](../../examples/browser-asr/) — پیاده‌سازی مرجع و تست‌شده
- [api تبدیل فایل صوتی به متن](transcription.md) اگر فایل ضبط‌شده دارید نه استریم زنده
- [احراز هویت](authentication.md) برای فرآیند Flash Token · [خطاها](errors.md)

</div>
