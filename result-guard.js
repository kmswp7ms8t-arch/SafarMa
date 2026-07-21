// Guard result generation so stale browser data can never leave the final button unresponsive.
const __smShowResult=showResult;
showResult=function(){
  normalizeProfile();
  try{
    return __smShowResult();
  }catch(error){
    console.error('SafarMa result generation failed:',error);
    const app=document.querySelector('#app');
    const bottom=document.querySelector('#bottom');
    if(app){
      app.innerHTML=`<section class="card verdict warn"><h2>${lang==='fa'?'نتیجه نیاز به بازسازی دارد':'The result needs to be rebuilt'}</h2><p>${lang==='fa'?'اطلاعات ذخیره‌شده از نسخه قبلی با نسخه جدید هماهنگ نبود. جواب‌های اصلی حفظ شده‌اند؛ روی دکمه زیر بزن تا نتیجه دوباره ساخته شود.':'Saved data from an older version was not fully compatible. Your main answers are preserved; tap below to rebuild the result.'}</p><button id="repairResult" class="primary full">${lang==='fa'?'بازسازی نتیجه':'Rebuild result'}</button><button id="restartWizard" class="secondary full" style="margin-top:10px">${lang==='fa'?'بازگشت و بررسی جواب‌ها':'Review answers'}</button><small class="tiny" style="display:block;margin-top:12px">${String(error?.message||error)}</small></section>`;
    }
    if(bottom)bottom.innerHTML='';
    document.querySelector('#repairResult')?.addEventListener('click',()=>{
      localStorage.setItem('sm-profile',JSON.stringify(normalizeProfile()));
      try{__smShowResult()}catch(e){console.error(e);localStorage.removeItem('sm-profile');location.reload()}
    });
    document.querySelector('#restartWizard')?.addEventListener('click',()=>{step=0;question()});
  }
};
