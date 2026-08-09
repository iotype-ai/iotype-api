<div align="center" dir="rtl">

# وب‌سرویس‌های iotype

**تشخیص گفتار، OCR، ترجمه و تبدیل متن به گفتار برای فارسی، انگلیسی و عربی — در قالب یک API ساده.**

[![وب‌سایت](https://img.shields.io/badge/website-iotype.com-6c5ce7)](https://iotype.com)
[![مستندات](https://img.shields.io/badge/docs-api--service-0984e3)](https://iotype.com/api-service)
[![دریافت توکن](https://img.shields.io/badge/%DB%B3%DB%B0%DB%B0-%D8%AA%D9%88%DA%A9%D9%86%20%D8%B1%D8%A7%DB%8C%DA%AF%D8%A7%D9%86-00b894)](https://iotype.com/api-service/authentication)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

[مستندات رسمی وب سرویس](https://iotype.com/api-service) · [اسپک OpenAPI](spec/openapi.yaml) · [اسپک AsyncAPI](spec/asyncapi.yaml) · [English](README.md)

</div>

---

<div dir="rtl">

## این ریپو چیست

هر آنچه برای اتصال به iotype لازم دارید: اسپک‌های ماشین‌خوان، راهنماهای کاربردی به فارسی و انگلیسی، نمونه‌های قابل اجرا، و SDK رسمی برای Python، JavaScript/TypeScript، PHP و Go.

اگر یک دستیار کدنویسی هوش مصنوعی هستید، از [`AGENTS.md`](AGENTS.md) شروع کنید.

## سرویس‌ها

| سرویس | نوع | آدرس | راهنما |
| --- | --- | --- | --- |
| تایپ صوتی همزمان | استریم WebSocket | `wss://iotype.com/socket/realtime` | [راهنما](docs/fa/realtime-asr.md) |
| تبدیل آنی فایل صوتی به متن | همزمان | `POST /io/v1/transcribe/instant` | [راهنما](docs/fa/transcription.md) |
| تبدیل فایل صوتی به متن | ناهمزمان | `POST /io/v1/transcribe` | [راهنما](docs/fa/transcription.md) |
| OCR | ناهمزمان | `POST /io/v1/ocr` | [راهنما](docs/fa/ocr.md) |
| ترجمه | همزمان | `POST /io/v1/translate` | [راهنما](docs/fa/translation.md) |
| تبدیل متن به صدا | همزمان | `POST /io/v1/synthesis` | [راهنما](docs/fa/text-to-speech.md) |
| لیست فایل‌ها | همزمان | `POST /io/v1/files` | [راهنما](docs/fa/files.md) |
| پیگیری یک فایل | همزمان | `POST /io/v1/file/track` | [راهنما](docs/fa/files.md) |

تمام endpointهای HTTP از متد `POST` استفاده می‌کنند و روی دامنه‌ی `https://iotype.com` قرار دارند.

## شروع سریع

توکن خود را از [پنل وب سرویس iotype](https://iotype.com/api-service/authentication) دریافت کنید. حساب‌های جدید ۳۰۰ توکن رایگان دارند.

</div>

```bash
export IOTYPE_TOKEN="your-token-here"

curl -X POST https://iotype.com/io/v1/translate \
  -H "Authorization: Bearer $IOTYPE_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d '{"source_lang":"fa","destination_lang":"en","text":"سلام دنیا"}'
```

```json
{ "result": "Hello world" }
```

<div dir="rtl">

### SDKها

</div>

```python
# Python
from iotype import Iotype
io = Iotype()                      # مقدار IOTYPE_TOKEN را از محیط می‌خواند
print(io.translate("سلام دنیا", "fa", "en"))
```

```js
// JavaScript
import { Iotype } from "@iotype-ai/sdk";
const io = new Iotype();
console.log(await io.translate("سلام دنیا", "fa", "en"));
```

```php
// PHP
$io = new Iotype\Client();
echo $io->translate('سلام دنیا', 'fa', 'en');
```

```go
// Go
io := iotype.New("")
out, _ := io.Translate(ctx, "سلام دنیا", "fa", "en")
```

<div dir="rtl">

نصب و شرح کامل متدها در پوشه‌ی [`sdk/`](sdk/).

نام رسمی پکیج‌ها در همه‌ی رجیستری‌ها `iotype-ai` است. روی PyPI دستور
`pip install iotype` هم کار می‌کند — توضیح در [`sdk/aliases/`](sdk/aliases/).

## احراز هویت

هر درخواست باید هدر زیر را داشته باشد:

</div>

```
Authorization: Bearer <TOKEN>
```

<div dir="rtl">

برای تایپ صوتی همزمان در مرورگر یا اپلیکیشن موبایل، یک **Flash Token** کوتاه‌عمر روی سرور خود بسازید و آن را به کلاینت بدهید. Access Token اصلی هرگز نباید در کدی که کنترلش با شما نیست قرار بگیرد.

دامنه‌ی Flash Token فقط وب‌سوکت تایپ صوتی همزمان است و هیچ endpoint‌ـی از نوع HTTP آن را نمی‌پذیرد. بنابراین تبدیل فایل صوتی به متن، OCR، ترجمه و تبدیل متن به صدا اعتبارنامه‌ی سمت کلاینت ندارند و باید از سرور شما فراخوانی شوند. جزئیات در [docs/fa/authentication.md](docs/fa/authentication.md).

## هزینه و توکن

محاسبه‌ی هزینه بر پایه‌ی مصرف توکن است. میزان مصرف هر درخواست به حجم داده، تعداد صفحات یا مدت فایل صوتی بستگی دارد. **درخواست‌های ناموفق محاسبه نمی‌شوند.** فهرست پکیج‌ها در [iotype.com/plans/api](https://iotype.com/plans/api).

## ساختار ریپو

</div>

```
spec/           اسپک OpenAPI 3.1 و AsyncAPI 3.0 — مرجع اصلی
docs/en/        راهنماهای انگلیسی
docs/fa/        راهنماهای فارسی
examples/curl/  یک اسکریپت قابل اجرا برای هر endpoint
examples/browser-asr/ کلاینت تست‌شده‌ی مرورگر برای پروتکل تایپ صوتی همزمان
postman/        کالکشن قابل ایمپورت Postman
sdk/python/     SDK رسمی پایتون
sdk/javascript/ SDK رسمی جاوااسکریپت/تایپ‌اسکریپت
sdk/php/        SDK رسمی PHP (فایل composer.json آن در ریشه است)
sdk/go/         SDK رسمی Go
sdk/aliases/    alias روی PyPI تا `pip install iotype` هم کار کند
site/           سورس سایت مستندات روی GitHub Pages
composer.json   مانیفست پکیج PHP؛ Packagist فقط فایل ریشه را می‌خواند
.gitattributes  بقیه‌ی فایل‌ها را از دانلود Composer خارج می‌کند
PUBLISHING.md   راهنمای انتشار در هر رجیستری
AGENTS.md       راهنما برای دستیارهای کدنویسی هوش مصنوعی
llms.txt        فهرست ماشین‌خوان برای LLMها
```

<div dir="rtl">

## مواردی که هنوز در مستندات رسمی نیامده

این موارد در اسپک با `x-unverified` علامت خورده‌اند و به تأیید نیاز دارند:

- آدرس endpoint صدور Flash Token، ساختار پاسخ و مدت اعتبار آن
- مقادیر دقیق `processes[].status`
- کدهای وضعیت HTTP و ساختار بدنه‌ی خطا فراتر از `401`
- محدودیت نرخ درخواست، حداکثر حجم فایل، حداکثر مدت صوت، حداکثر تعداد صفحات
- میزان مصرف توکن به ازای هر صفحه، هر دقیقه صوت و هر کاراکتر

## درباره‌ی آی او تایپ

[**آی او تایپ**](https://iotype.com) سرویس‌های هوش مصنوعی و پردازش زبان طبیعی برای فارسی، انگلیسی و عربی ارائه می‌دهد — بدون نیاز به زیرساخت یادگیری ماشین اختصاصی. توسعه‌دهندگان می‌توانند پردازش گفتار و سند را مستقیماً در وب‌اپلیکیشن، اپلیکیشن موبایل و سرویس‌های سمت سرور خود ادغام کنند.

| | |
| --- | --- |
| [وب سرویس تایپ صوتی همزمان](https://iotype.com/api-service/speech-to-text) | تبدیل بلادرنگ گفتار فارسی به متن روی WebSocket |
| [api تبدیل فایل صوتی به متن](https://iotype.com/api-service/transcription) | تبدیل فایل MP3 به متن، همراه با خلاصه‌سازی اختیاری |
| [وب سرویس OCR فارسی](https://iotype.com/api-service/ocr) | استخراج متن از پی‌دی‌اف اسکن‌شده و عکس |
| [api ترجمه ماشینی](https://iotype.com/api-service/translation) | فارسی ⇄ انگلیسی ⇄ عربی |
| [api تبدیل متن به صدا](https://iotype.com/api-service/text-to-speech) | یازده صدای فارسی، دو لحن |
| [تعرفه وب سرویس](https://iotype.com/plans/api) | مبتنی بر توکن؛ ۳۰۰ توکن رایگان هنگام ثبت‌نام |

مستندات کامل سرویس‌ها در **[iotype.com/api-service](https://iotype.com/api-service)** قرار دارد. این ریپو همان مستندات را به شکل ماشین‌خوان بازتاب می‌دهد و SDK اضافه می‌کند.

## انتشار

راهنمای انتشار در هر رجیستری: [`PUBLISHING.md`](PUBLISHING.md).

## لایسنس

MIT — فایل [LICENSE](LICENSE).

</div>

---

<div align="center">

نگهداری‌شده توسط [آی او تایپ](https://iotype.com) · [مستندات وب سرویس](https://iotype.com/api-service) · [دریافت توکن وب سرویس](https://iotype.com/api-service/authentication) · [تعرفه وب سرویس](https://iotype.com/plans/api)

</div>
