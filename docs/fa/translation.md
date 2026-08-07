<div dir="rtl">

# ترجمه

ترجمه‌ی متن میان فارسی، انگلیسی و عربی. همزمان — نتیجه در همان پاسخ برمی‌گردد.

**آدرس:** `POST /io/v1/translate`

## درخواست

</div>

```bash
curl -X POST https://iotype.com/io/v1/translate \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d '{
        "source_lang": "fa",
        "destination_lang": "en",
        "text": "سلام! امروز هوا بسیار عالی است."
      }'
```

<div dir="rtl">

**بدنه** — application/json

| پارامتر | نوع | الزامی | مقادیر |
| --- | --- | --- | --- |
| `source_lang` | string | بله | `fa`، `en`، `ar` |
| `destination_lang` | string | بله | `fa`، `en`، `ar` |
| `text` | string | بله | متنی که ترجمه می‌شود |

هر ترکیبی از این سه زبان، در هر دو جهت، پشتیبانی می‌شود.

## پاسخ

</div>

```json
{ "result": "Hello! The weather is excellent today." }
```

<div dir="rtl">

## SDK

</div>

```python
io.translate("سلام دنیا", "fa", "en")
```

```js
await io.translate("سلام دنیا", "fa", "en");
```

```php
$io->translate('سلام دنیا', 'fa', 'en');
```

```go
io.Translate(ctx, "سلام دنیا", "fa", "en")
```

<div dir="rtl">

## نکته

رشته‌ی برگشتی را دست‌نخورده نگه دارید. خروجی فارسی و عربی راست‌به‌چپ است؛ آن را معکوس نکنید، کاراکترهای کنترلی دوجهته را حذف نکنید و پیش از نمایش نرمال‌سازی نکنید. به‌جای آن روی المان نگه‌دارنده `dir="rtl"` بگذارید.

## مواردی که در مستندات نیامده

- حداکثر طول متن در هر درخواست
- امکان یا عدم امکان ارسال چند متن در یک فراخوانی
- میزان مصرف توکن به ازای هر کاراکتر یا کلمه

</div>

<div dir="rtl">

---

## همچنین ببینید

- [وب سرویس ترجمه آنلاین (api ترجمه)](https://iotype.com/api-service/translation) — مستندات رسمی آی او تایپ
- [تبدیل متن به صدا](text-to-speech.md) برای خواندن متن ترجمه‌شده
- [OCR](ocr.md) برای ترجمه‌ی متن استخراج‌شده از یک سند

</div>
