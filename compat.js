// SafarMa profile migration and runtime compatibility layer.
const __smDefaults={origin:'DOH',customOrigin:'',adults:2,children:0,passport:'Iran',passportExpiry:'',secondPassport:'',resStatus:'citizen',resCountry:'',resExpiry:'',start:'2026-08-06',days:6,flex:3,budget:13000,mode:'open',wanted:'',regions:['near'],styles:['nature','relax','romantic'],flight:'prefer',maxHours:9,stay:'four',transport:'needed',food:'balanced',halal:true,priority:'overall'};
function normalizeProfile(){
  const old=p&&typeof p==='object'?p:{};
  const preferred=Array.isArray(old.preferredDestinations)?old.preferredDestinations.join(', '):(old.preferredDestinations||old.customDestination||old.destination||old.wanted||'');
  const migrated={...__smDefaults,...old,
    origin:old.origin||old.originAirport||__smDefaults.origin,
    adults:Number(old.adults??old.travelers??__smDefaults.adults)||__smDefaults.adults,
    children:Number(old.children??0)||0,
    passport:old.passport||old.nationality||__smDefaults.passport,
    passportExpiry:old.passportExpiry||old.passExpiry||'',
    secondPassport:old.secondPassport||'',
    resStatus:old.resStatus||old.residenceStatus||__smDefaults.resStatus,
    resCountry:old.resCountry||old.residenceCountry||'',
    resExpiry:old.resExpiry||old.residenceExpiry||'',
    start:old.start||old.startDate||old.date||__smDefaults.start,
    days:Number(old.days??old.tripDays??__smDefaults.days)||__smDefaults.days,
    budget:Number(old.budget??old.totalBudget??__smDefaults.budget)||__smDefaults.budget,
    mode:old.mode||old.destinationMode||__smDefaults.mode,
    wanted:typeof preferred==='string'?preferred:'',
    styles:Array.isArray(old.styles)?old.styles:(Array.isArray(old.travelStyles)?old.travelStyles:__smDefaults.styles),
    flight:old.flight||old.flightPreference||__smDefaults.flight,
    maxHours:Number(old.maxHours??old.maxJourneyHours??__smDefaults.maxHours)||__smDefaults.maxHours,
    stay:old.stay||old.accommodation||__smDefaults.stay,
    transport:old.transport||old.transportPreference||__smDefaults.transport,
    food:old.food||old.foodPreference||__smDefaults.food,
    halal:typeof old.halal==='boolean'?old.halal:__smDefaults.halal,
    priority:old.priority||old.finalPriority||__smDefaults.priority
  };
  if(!['open','ideas'].includes(migrated.mode)) migrated.mode=preferred?'ideas':'open';
  if(!Array.isArray(migrated.styles)) migrated.styles=[];
  migrated.styles=migrated.styles.filter(Boolean).slice(0,3);
  if(!migrated.styles.length) migrated.styles=['nature'];
  if(!Number.isFinite(migrated.budget)||migrated.budget<1000)migrated.budget=__smDefaults.budget;
  if(!Number.isFinite(migrated.days)||migrated.days<3)migrated.days=__smDefaults.days;
  if(!Number.isFinite(migrated.maxHours)||migrated.maxHours<2)migrated.maxHours=__smDefaults.maxHours;
  p=migrated;
  localStorage.setItem('sm-profile',JSON.stringify(p));
  return p;
}
normalizeProfile();
window.addEventListener('error',event=>{console.error('SafarMa runtime error:',event.error||event.message)});
