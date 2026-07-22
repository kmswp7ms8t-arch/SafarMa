# SafarMa — Powered by Belink AI

## وضعیت تحویل

- اپ عمومی: `https://kmswp7ms8t-arch.github.io/SafarMa/?v=8`
- Frontend روی GitHub Pages منتشر می‌شود.
- Backend واقعی در `belink-ai-v2/backend` قرار دارد.
- Blueprint انتشار Render در `render.yaml` قرار دارد.
- کلید OpenAI هرگز نباید داخل Frontend یا Repository قرار بگیرد.

## انتشار Backend روی Render

1. وارد حساب Render شوید.
2. گزینه **New > Blueprint** را انتخاب کنید.
3. Repository زیر را انتخاب کنید:
   `kmswp7ms8t-arch/SafarMa`
4. Render فایل `render.yaml` را تشخیص می‌دهد.
5. مقدار Secret زیر را در Render وارد کنید:
   `OPENAI_API_KEY`
6. Deploy را اجرا کنید.
7. پس از آماده‌شدن سرویس، این آدرس‌ها باید پاسخ موفق بدهند:
   - `/health`
   - `/ready`

## اتصال Backend به اپ

پس از دریافت آدرس Render، یکی از دو روش زیر را انجام دهید:

### روش دائمی

در فایل `belink-runtime.js` مقدار `apiBase` را برابر URL سرویس قرار دهید و Commit کنید.

### روش تست فوری روی همان دستگاه

داخل اپ روی **Belink AI** بزنید، بخش **اتصال امن Backend** را باز کنید، URL سرویس را وارد کنید و **ذخیره و تست** را بزنید.

## کنترل نهایی

- زبان فارسی و انگلیسی
- RTL و LTR
- مبدأ، ملیت، پاسپورت و اقامت
- اعتبار پاسپورت براساس قانون مقصد
- ویزا و ترانزیت
- امنیت
- پرواز و هتل
- آب‌وهوا
- هزینه کامل
- دیدنی‌ها، غذا، فعالیت و ویدئو
- نتیجه شدنی / مشروط / نشدنی
- Chat با Belink Commander
- نمایش منابع، تعارض‌ها و موارد نامشخص

---

## English handoff

- Public frontend: `https://kmswp7ms8t-arch.github.io/SafarMa/?v=8`
- The real backend is under `belink-ai-v2/backend`.
- `render.yaml` provides the deployment blueprint.
- Keep `OPENAI_API_KEY` server-side only.
- After deployment, set the backend URL in `belink-runtime.js`, or enter it through the in-app secure backend connection panel for device-local testing.
