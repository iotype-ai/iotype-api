<div dir="rtl">

# تبدیل فایل صوتی به متن

دو endpoint فایل‌های MP3 را به متن تبدیل می‌کنند. تفاوتشان در تأخیر و دقت است.

| | آنی | استاندارد |
| --- | --- | --- |
| آدرس | `POST /io/v1/transcribe/instant` | `POST /io/v1/transcribe` |
| نوع | همزمان | ناهمزمان |
| مناسب برای | فایل‌های کوتاه | فایل‌های طولانی |
| دقت | خوب | بالاتر |
| خلاصه‌سازی | ندارد | اختیاری |
| انتخاب زبان | خودکار | `source_lang` |

هر دو از فارسی، انگلیسی و عربی پشتیبانی می‌کنند.

**کیفیت ورودی تعیین‌کننده است.** صوت باید یک گوینده داشته باشد، بدون نویز محیطی و کاملاً واضح باشد. فایل‌های پرنویز یا چندگوینده کیفیت خروجی هر دو سرویس را پایین می‌آورند.

---

## تبدیل آنی

آپلود کنید، متن را در همان پاسخ بگیرید.

</div>

```bash
curl -X POST https://iotype.com/io/v1/transcribe/instant \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -F "file=@sample.mp3"
```

<div dir="rtl">

**بدنه** — multipart/form-data

| پارامتر | نوع | الزامی | توضیح |
| --- | --- | --- | --- |
| `file` | فایل | بله | MP3 |

**پاسخ**

</div>

```json
{ "result": "سلام، حال شما چطور است؟" }
```

<div dir="rtl">

---

## تبدیل استاندارد

آپلود کنید، شناسه‌ی فایل بگیرید، سپس نتیجه را پیگیری کنید.

</div>

```bash
curl -X POST https://iotype.com/io/v1/transcribe \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -F "file=@meeting.mp3" \
  -F "should_summarize=true" \
  -F "source_lang=fa"
```

<div dir="rtl">

**بدنه** — multipart/form-data

| پارامتر | نوع | الزامی | توضیح |
| --- | --- | --- | --- |
| `file` | فایل | بله | MP3 |
| `should_summarize` | boolean | خیر | تولید خلاصه در کنار متن |
| `source_lang` | string | خیر | `fa`، `en` یا `ar` |

**پاسخ** — بلافاصله برمی‌گردد و **شامل متن نیست**:

</div>

```json
{
  "file": {
    "uuid": "9f1c2d84-1f4e-4a1b-9d0e-3f6a2b7c8e11",
    "name": "1712345678_9f1c2d84.mp3",
    "filename": "meeting.mp3",
    "processes": [
      { "type": "transcribe", "status": "processing", "result": null }
    ]
  }
}
```

<div dir="rtl">

### دریافت نتیجه

با استفاده از `uuid`، endpoint [`POST /io/v1/file/track`](files.md) را تا زمانی که یکی از پروسه‌ها مقدار `result` غیر خالی داشته باشد، فراخوانی کنید.

</div>

```bash
curl -X POST https://iotype.com/io/v1/file/track \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"uuid":"9f1c2d84-1f4e-4a1b-9d0e-3f6a2b7c8e11"}'
```

```json
{
  "file": {
    "uuid": "9f1c2d84-1f4e-4a1b-9d0e-3f6a2b7c8e11",
    "processes": [
      { "type": "transcribe", "status": "done", "result": "متن کامل جلسه ..." },
      { "type": "summarize",  "status": "done", "result": "خلاصه جلسه ..." }
    ]
  }
}
```

<div dir="rtl">

پروسه‌ها را با `type` پیدا کنید، نه با شماره‌ی خانه در آرایه. وقتی `should_summarize` فعال باشد بیش از یک پروسه وجود دارد.

فاصله‌ی polling را از ۵ ثانیه شروع کنید و تا سقف ۶۰ ثانیه دو برابر کنید. زمان پردازش با مدت فایل رابطه‌ی مستقیم دارد.

SDKها این حلقه را پیاده کرده‌اند:

</div>

```python
result = io.transcribe("meeting.mp3", summarize=True, source_lang="fa", wait=True)
```

<div dir="rtl">

---

## کدام را انتخاب کنیم

**آنی** را وقتی به‌کار ببرید که کاربر پشت صفحه منتظر است و فایل کوتاه است — یک پیام صوتی، یک فرمان، یک یادداشت.

**استاندارد** را وقتی به‌کار ببرید که دقت مهم‌تر از سرعت است، فایل طولانی است، یا به خلاصه نیاز دارید — جلسات، مصاحبه‌ها، سخنرانی‌ها، ضبط تماس‌ها.

---

## مواردی که در مستندات نیامده

- حداکثر حجم فایل و حداکثر مدت صوت برای هر دو endpoint
- آستانه‌ای که از آن به بعد سرویس «آنی» دیگر آنی نیست
- میزان مصرف توکن به ازای هر دقیقه صوت
- وجود یا نبود webhook به‌عنوان جایگزین polling

</div>

<div dir="rtl">

---

## همچنین ببینید

- [وب سرویس تبدیل فایل صوتی به متن](https://iotype.com/api-service/transcription) — مستندات رسمی آی او تایپ
- [تایپ صوتی همزمان](realtime-asr.md) برای استریم زنده به‌جای فایل ضبط‌شده
- [فایل‌ها و پردازش ناهمزمان](files.md) · [خطاها](errors.md)

</div>
