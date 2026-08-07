<div dir="rtl">

# تبدیل متن به صدا

تولید فایل MP3 از متن، با صدای گوینده و لحن دلخواه. همزمان — پاسخ شامل آدرس فایل صوتی است.

**آدرس:** `POST /io/v1/synthesis`

## درخواست

</div>

```bash
curl -X POST https://iotype.com/io/v1/synthesis \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d '{
        "tone": "general",
        "speaker": "tanaz",
        "text": "سلام! امروز هوا بسیار عالی است."
      }'
```

<div dir="rtl">

**بدنه** — application/json

| پارامتر | نوع | الزامی | مقادیر |
| --- | --- | --- | --- |
| `tone` | string | خیر | `general`، `formal` |
| `speaker` | string | خیر | فهرست گویندگان |
| `text` | string | بله | متنی که خوانده می‌شود |

## گویندگان

| | | |
| --- | --- | --- |
| `behrooz` | `mehran` | `farshid` |
| `sara` | `mitra` | `siavash` |
| `shirin` | `kaveh` | `amir` |
| `tanaz` | `mahsa` | |

مستندات رسمی این صداها را بر اساس جنسیت یا سبک برچسب‌گذاری نکرده است — با متن خودتان امتحان کنید و انتخاب نمایید.

## لحن

| مقدار | مناسب برای |
| --- | --- |
| `general` | محتوای محاوره‌ای، دستیارها، روایت غیررسمی |
| `formal` | اعلان‌ها، اخبار، اطلاعیه‌های رسمی، پیام‌های IVR |

## پاسخ

</div>

```json
{ "url": "https://iotype.com/storage/tts/9f1c2d84.mp3" }
```

<div dir="rtl">

اگر به فایل به‌صورت بلندمدت نیاز دارید، آن را دانلود کنید. مدت نگهداری فایل‌های تولیدشده اعلام نشده است — فرض نکنید این آدرس دائمی است.

## SDK

</div>

```python
url = io.synthesize("سلام دنیا", speaker="tanaz", tone="general")
io.download(url, "narration.mp3")
```

```js
const url = await io.synthesize("سلام دنیا", { speaker: "tanaz" });
```

<div dir="rtl">

## مواردی که در مستندات نیامده

- حداکثر طول متن در هر درخواست
- مدت نگهداری فایل‌های تولیدشده
- نرخ نمونه‌برداری و بیت‌ریت خروجی MP3
- پشتیبانی از SSML یا کنترل سرعت و زیروبمی صدا
- میزان مصرف توکن به ازای هر کاراکتر

</div>

<div dir="rtl">

---

## همچنین ببینید

- [وب سرویس تبدیل متن به صدا — api و نمونه صداها](https://iotype.com/api-service/text-to-speech) — مستندات رسمی آی او تایپ
- [ترجمه](translation.md) برای خواندن متن به زبان دیگر
- [پکیج‌های توکن وب سرویس](https://iotype.com/plans/api)

</div>
