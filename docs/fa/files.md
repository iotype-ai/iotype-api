<div dir="rtl">

# فایل‌ها و پردازش‌های ناهمزمان

سرویس‌های `POST /io/v1/ocr` و `POST /io/v1/transcribe` نتیجه را مستقیماً برنمی‌گردانند. آن‌ها یک **شناسه‌ی فایل** می‌دهند و نتیجه بعداً داخل `file.processes` ظاهر می‌شود.

دو endpoint برای پیگیری این پردازش‌ها وجود دارد.

## آبجکت File

</div>

```json
{
  "uuid": "9f1c2d84-1f4e-4a1b-9d0e-3f6a2b7c8e11",
  "name": "1712345678_9f1c2d84.mp3",
  "filename": "meeting.mp3",
  "processes": [
    { "type": "transcribe", "status": "done", "result": "..." },
    { "type": "summarize",  "status": "done", "result": "..." }
  ]
}
```

<div dir="rtl">

| فیلد | معنی |
| --- | --- |
| `uuid` | شناسه‌ی پیگیری فایل — آن را ذخیره کنید |
| `name` | نام فایل روی سرورهای iotype |
| `filename` | نام اصلی فایلی که آپلود کرده‌اید |
| `processes` | یک ورودی به ازای هر عملیات در حال انجام روی فایل |

هر پروسه پس از اتمام، مقدار `result` می‌گیرد. **پایان کار را با `result != null` تشخیص دهید.** مقادیر دقیق `status` در مستندات رسمی منتشر نشده، پس شرط‌گذاری روی آن‌ها شکننده است.

وقتی `should_summarize` فعال بوده، یک پروسه‌ی اضافی برای خلاصه وجود خواهد داشت. **پروسه‌ها را با `type` پیدا کنید، هرگز با ایندکس آرایه.**

---

## پیگیری یک فایل

**آدرس:** `POST /io/v1/file/track`

</div>

```bash
curl -X POST https://iotype.com/io/v1/file/track \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"uuid":"9f1c2d84-1f4e-4a1b-9d0e-3f6a2b7c8e11"}'
```

<div dir="rtl">

**بدنه**

| پارامتر | نوع | الزامی |
| --- | --- | --- |
| `uuid` | string | بله |

**پاسخ:** `{ "file": File }`

---

## لیست تمام فایل‌ها

**آدرس:** `POST /io/v1/files`

تمام فایل‌هایی که این توکن ارسال کرده، همراه با پروسه‌هایشان برمی‌گردد. پارامتری نمی‌گیرد — یک آبجکت JSON خالی بفرستید.

</div>

```bash
curl -X POST https://iotype.com/io/v1/files \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

<div dir="rtl">

**پاسخ:** `{ "files": [File] }`

توجه کنید که متد `POST` است نه `GET`، و بدنه `{}` است نه خالی.

---

## polling درست

</div>

```
backoff = ۵ ثانیه
deadline = اکنون + timeout

حلقه:
  file = track(uuid)
  process = اولین پروسه‌ای که type آن با درخواست شما یکی است
  اگر process.result خالی نبود:
      نتیجه را برگردان
  اگر از deadline گذشتیم:
      خطای Timeout
  sleep(backoff)
  backoff = min(backoff * 2, 60)
```

<div dir="rtl">

قواعد:

- **هرگز در حلقه‌ی تنگ polling نکنید.** از ۵ ثانیه شروع کنید و فاصله را زیاد کنید.
- **سقف backoff را ۶۰ ثانیه** بگذارید تا کار طولانی هم به‌موقع تحویل داده شود.
- **یک مهلت کلی تعیین کنید.** زمان پردازش با حجم ورودی رابطه‌ی مستقیم دارد؛ یک فایل دو ساعته کار سی‌ثانیه‌ای نیست.
- **مقدار `uuid` را ماندگار ذخیره کنید.** اگر پروسه‌ی شما ری‌استارت شد، به‌جای آپلود دوباره و پرداخت مضاعف، پیگیری را ادامه دهید.

تمام SDKهای این ریپو این حلقه را پیاده کرده‌اند — کافی است `wait=true` بدهید.

</div>

```python
text = io.ocr("contract.pdf", wait=True, timeout=1800)
```

<div dir="rtl">

## مواردی که در مستندات نیامده

- فهرست کامل مقادیر `processes[].status`
- فهرست کامل مقادیر `processes[].type`
- صفحه‌بندی در `/io/v1/files` و نحوه‌ی آن
- مدت نگهداری فایل‌ها و نتایج
- وجود یا نبود webhook به‌عنوان جایگزین polling

</div>

<div dir="rtl">

---

## همچنین ببینید

- [مستندات وب سرویس‌های آی او تایپ](https://iotype.com/api-service) — همه‌ی سرویس‌ها
- [OCR](ocr.md) و [تبدیل فایل صوتی](transcription.md) — دو سرویسی که از این روند استفاده می‌کنند
- [خطاها و پایداری](errors.md) برای سیاست تلاش مجدد و timeout

</div>
