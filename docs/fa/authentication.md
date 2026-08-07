<div dir="rtl">

# احراز هویت

هر درخواست به iotype با یک توکن Bearer احراز هویت می‌شود.

</div>

```
Authorization: Bearer <TOKEN>
```

<div dir="rtl">

توکن را از [صفحه‌ی احراز هویت وب سرویس](https://iotype.com/api-service/authentication) در پنل خود بسازید. حساب‌های جدید ۳۰۰ توکن رایگان دارند.

## هدرهای الزامی

| هدر | مقدار | چه زمانی |
| --- | --- | --- |
| `Authorization` | `Bearer <TOKEN>` | همیشه |
| `Accept` | `application/json` | همیشه |
| `X-Requested-With` | `XMLHttpRequest` | همیشه |
| `Content-Type` | `application/json` | فقط endpointهای JSON |

برای آپلود‌های multipart هدر `Content-Type` را **خودتان تنظیم نکنید** — کتابخانه‌ی HTTP باید آن را بسازد تا مقدار boundary درست درج شود.

## نگهداری توکن

توکن را از متغیر محیطی بخوانید و هرگز آن را commit نکنید.

</div>

```bash
# .env — فایل .env را در .gitignore قرار دهید
IOTYPE_TOKEN=1|xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

<div dir="rtl">

اگر توکن به هر شکلی افشا شد — در اسکرین‌شات، در commit، یا در لاگ — بلافاصله از پنل توکن جدید بسازید. ساخت توکن جدید، توکن قبلی را باطل می‌کند.

## Access Token در برابر Flash Token

سرویس تایپ صوتی همزمان دو نوع اعتبارنامه می‌پذیرد. انتخاب اشتباه میان این دو، رایج‌ترین خطای امنیتی در کار با این API است.

### Access Token

کلید بلندمدت شماست. برای این موارد استفاده کنید:

- تمام endpointهای HTTP
- اتصال WebSocket که **از سرور خودتان** برقرار می‌شود

هرگز آن را در مرورگر، اپلیکیشن موبایل یا نرم‌افزار دسکتاپ قرار ندهید. هر چیزی که روی دستگاه کاربر اجرا شود، توسط همان کاربر قابل خواندن است.

### Flash Token

توکن کوتاه‌عمر و یک‌بارمصرف که برای یک اتصال ASR صادر می‌شود. برای این موارد:

- مرورگر
- اپلیکیشن اندروید و iOS
- نرم‌افزار دسکتاپ

مسیر کار:

</div>

```
سرور شما   --(Access Token)-->  iotype       صدور Flash Token
سرور شما   --(Flash Token)--->  کلاینت شما
کلاینت شما --(Flash Token)--->  wss://iotype.com/socket/realtime
```

<div dir="rtl">

چون Flash Token به‌سرعت منقضی می‌شود و قابل استفاده‌ی مجدد نیست، افشای آن ریسکی به‌مراتب کمتر از افشای Access Token دارد.

**هدرهای درخواست صدور Flash Token:**

</div>

```
Authorization: Bearer <ACCESS_TOKEN>
Accept: application/json
X-Requested-With: XMLHttpRequest
```

<div dir="rtl">

> **شکاف مستندات:** آدرس endpoint صدور Flash Token، ساختار پاسخ و مدت اعتبار آن در مستندات رسمی منتشر نشده است. در اسپک این ریپو به‌صورت `POST /io/v1/flash-token` با علامت `x-unverified` مدل شده. پیش از اتکا به آن، با یک فراخوانی واقعی تأیید کنید.

## خطا

کد `401 Unauthorized` در این حالت‌ها بازگردانده می‌شود: نبود هدر، توکن نامعتبر، توکن منقضی‌شده، **یا اتمام اعتبار توکن**.

هر چهار حالت را در پیام خطای خود پوشش دهید. کاربری که اعتبارش تمام شده و پیام «توکن نامعتبر» می‌بیند، سراغ مشکل اشتباهی می‌رود.

درخواست‌های ناموفق توکن مصرف نمی‌کنند.

</div>

<div dir="rtl">

---

## همچنین ببینید

- [ساخت توکن وب سرویس](https://iotype.com/api-service/authentication) — پنل آی او تایپ
- [پکیج و تعرفه توکن وب سرویس](https://iotype.com/plans/api)
- [خطاها و پایداری](errors.md) · [تایپ صوتی همزمان](realtime-asr.md)

</div>
