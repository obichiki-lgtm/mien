# Artifact「Pomo Timer」の HTML を GitHub Pages 用に変換する: python3 tools/port_pomo.py <artifact.html> pomo/index.html
import sys
src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, (old[:80], n)
    h = h.replace(old, new)

# 1. document head: lang, Firebase SDK, cloud shim
FB = '''<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore-compat.js"></script>
<script>
/* Cloud sync outside claude.ai: Firebase Auth (Google) + Firestore, collection pomo/{uid}/docs */
window.PomoCloud=(()=>{
  const config={
    apiKey:"AIzaSyAP51tb-FcRmc1RukwczxfxzUdOkE7yf4g",
    authDomain:"my-study-app-6a0b6.firebaseapp.com",
    projectId:"my-study-app-6a0b6",
    storageBucket:"my-study-app-6a0b6.firebasestorage.app",
    messagingSenderId:"441129563668",
    appId:"1:441129563668:web:48cc07f882bff1785e5901"};
  if(!window.firebase)return null;
  try{firebase.initializeApp(config)}catch(e){return null}
  const auth=firebase.auth(),fs=firebase.firestore();
  const ready=new Promise(res=>{const off=auth.onAuthStateChanged(u=>{off();res(u)})});
  return {
    ready,
    get user(){return auth.currentUser},
    col(uid){return fs.collection('pomo/'+uid+'/docs')},
    async schedDoc(uid){const d=await fs.doc('users/'+uid).get();return d.exists?d.data():null},
    async signIn(){const p=new firebase.auth.GoogleAuthProvider();p.setCustomParameters({prompt:'select_account'});return (await auth.signInWithPopup(p)).user},
    signOut(){return auth.signOut()},
    async hasCloud(uid){return (await fs.doc('pomo/'+uid+'/docs/state').get()).exists},
    sendFeedback(o){return fs.collection('feedback').add(Object.assign({},o,{at:firebase.firestore.FieldValue.serverTimestamp(),uid:auth.currentUser?auth.currentUser.uid:null,processed:false}))},
    async deleteCloud(uid){const q=await fs.collection('pomo/'+uid+'/docs').get(),b=fs.batch();q.docs.forEach(d=>b.delete(d.ref));await b.commit()}};
})();
</script>
'''
rep('<!doctype html><html><head>', '<!doctype html><html lang="ja"><head>')
PWA = '''<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#D9452B">
<link rel="icon" href="icons/icon-192.png" type="image/png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Pomo Timer">
<script>/* app icon, tab icon, bar color and install manifest follow the theme color (tools/make_pomo_icons.py) */
window.pomoIcon=function(a){var C={tomato:'#D9452B',ocean:'#2268B8',forest:'#2E8656',grape:'#7448BF',sumi:'#26302C'};if(!C[a])a='tomato';
  var q=function(s){return document.querySelector(s)},d=a==='tomato'?'icons/':'icons/'+a+'/';
  q('link[rel="manifest"]').href=a==='tomato'?'manifest.webmanifest':'manifest-'+a+'.webmanifest';
  q('link[rel="icon"]').href=d+'icon-192.png';q('link[rel="apple-touch-icon"]').href=d+'apple-touch-icon.png';q('meta[name="theme-color"]').content=C[a]};
try{pomoIcon(JSON.parse(localStorage.getItem('pf2_state')).settings.accent)}catch(e){}</script>
<script>if('serviceWorker' in navigator&&(location.protocol==='https:'||location.hostname==='localhost'))addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(()=>{}))</script>
'''
# PWA tags must be in <head> (Chrome ignores <link rel="manifest"> in <body>; the artifact puts <title> in <body>)
rep('</style></head><body>', '</style>\n' + PWA + '</head><body>')
rep('<title>Pomo Timer</title>', '<title>Pomo Timer</title>\n' + FB)

# 2. Sync.init: claude.ai runtime when present, Firebase otherwise
rep("""    if(!window.claude||!window.claude.use){this.set('','この端末に保存','同期は claude.ai で開いたときに使えます');return}""",
"""    if(!window.claude||!window.claude.use){
      const pc=window.PomoCloud;if(!pc){this.set('','この端末に保存');return}
      const u=await pc.ready;
      if(!u){this.set('login','この端末に保存 · ログイン','押すと Google でログインし、端末間で同期します');return}
      this.attach(u);return}""")

# 3. settings row: account status + login / logout
rep("""<div class="pr"><span>同期<small>${Sync.col?'同じアカウントで開いた端末どうしで自動同期しています':'この端末のブラウザに保存中。claude.ai にサインインして開くと同期されます'}</small></span></div>""",
"""<div class="pr"><span>同期<small>${Sync.col?(window.PomoCloud&&PomoCloud.user?esc(PomoCloud.user.email||'')+' でログイン中。同じアカウントの端末どうしで自動同期しています':'同じアカウントで開いた端末どうしで自動同期しています'):(window.PomoCloud?'この端末のブラウザに保存中。Google でログインすると端末間で同期されます':'この端末のブラウザに保存中。claude.ai にサインインして開くと同期されます')}</small></span>${window.PomoCloud?(PomoCloud.user?'<button class="btn" id="d_logout">ログアウト</button>':'<button class="btn accent" id="d_login">Google でログイン</button>'):''}</div>""")

# 4. handlers
rep("""  if(t.id==='d_export')exportData();if(t.id==='d_import')$('#importFile').click();""",
"""  if(t.id==='d_export')exportData();if(t.id==='d_import')$('#importFile').click();
  if(t.id==='d_login'){cloudLogin();return}
  if(t.id==='d_logout'){cloudLogout();return}""")

rep("""async function saveFile(name,data){""",
"""if(window.PomoCloud&&new URLSearchParams(location.search).get('import')==='sched'){history.replaceState(null,'',location.pathname);PomoCloud.ready.then(()=>setTimeout(importSched,1200))}
/*@cloud*/
async function saveFile(name,data){""")

rep('.modal .box p{margin:0;font-size:14.5px}','.modal .box p{margin:0;font-size:14.5px;white-space:pre-line}')
# settings: denser rows, full width, masonry columns (no holes between panels of different heights)
rep('.pr input[type=range]{width:130px;accent-color:var(--focus)}','''.pr input[type=range]{width:130px;accent-color:var(--focus)}
.pgrid,.prefhead{max-width:1180px}
@media(min-width:900px){.pgrid{display:block;columns:2;column-gap:14px}.pgrid>*{break-inside:avoid;margin-bottom:14px}}
@media(min-width:1140px){.pgrid{columns:3}}
.pgrid .panel{padding:12px 16px}.pgrid .ph{margin-bottom:4px}
.pr{padding:6px 0;line-height:1.45}.pr input,.pr select{padding:5px 9px}''')
# settings row + importer: 学習スケジューラー (root index.html) -> Pomo Timer
rep("""<div class="pr"><span>バックアップ<small>JSONファイルで保存・復元</small></span>""",
"""${window.PomoCloud?'<div class="pr"><span>学習スケジューラーから引き継ぐ<small>復習の予定・未完了のタスク・メモを取り込みます（何度押しても重複しません）</small></span><button class="btn" id="d_sched">引き継ぐ</button></div>':''}<div class="pr"><span>バックアップ<small>JSONファイルで保存・復元</small></span>""")
rep("""  if(t.id==='d_login'){cloudLogin();return}""","""  if(t.id==='d_login'){cloudLogin();return}
  if(t.id==='d_sched'){importSched();return}""")
# brand: tap to reload (latest app version + latest synced data), after sending pending writes
rep('<div class="brand"><i></i>Pomo Timer</div>','<div class="brand" id="brand" role="button" tabindex="0" title="押すと再読み込みします"><i></i>Pomo Timer</div>')
rep('.brand i{','#brand{cursor:pointer;border-radius:10px}#brand:active{opacity:.6}\n.brand i{')
rep("""/*@cloud*/""","""/*@cloud*/
async function reloadApp(){toast('再読み込みしています…');try{if(Sync.col)await Sync.flushAll()}catch(e){}location.reload()}
$('#brand').addEventListener('click',reloadApp);$('#brand').addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();reloadApp()}});""")
rep("""/*@cloud*/""","""/*@cloud*/
/* 学習スケジューラー → Pomo Timer. Source: Firestore users/{uid} when signed in, else this origin's localStorage.
   tasks{name,reviews[],doneDates[],startDate} -> st.reviews, unfinished todos{name,date} -> st.tasks, memo -> st.memos */
async function loadSched(){let d=null;
  if(window.PomoCloud&&PomoCloud.user){try{d=await PomoCloud.schedDoc(PomoCloud.user.uid)}catch(e){}}
  if(!d){try{const g=k=>JSON.parse(localStorage.getItem(k)||'null');const tasks=g('myTasks'),todos=g('myTodos'),memo=localStorage.getItem('myMemo');if(tasks||todos||memo)d={tasks,todos,memo}}catch(e){}}
  return d}
function schedPlan(d){const today=todayKey(),seen=new Set();
  st.reviews.forEach(x=>x.fromSched&&seen.add(x.fromSched));st.tasks.forEach(x=>x.fromSched&&seen.add(x.fromSched));st.memos.forEach(x=>x.fromSched&&seen.add(x.fromSched));
  const days=(a,b)=>Math.round((k2d(b)-k2d(a))/86400000),at=k=>k2d(k).getTime()+12*3600000;
  const rv=[],tk=[],mm=[];
  for(const t of (d.tasks||[])){if(!t||!t.name)continue;const key='sched-r-'+t.id;if(seen.has(key))continue;
    const done=[...new Set(t.doneDates||[])].sort(),last=done[done.length-1]||t.startDate||today;
    const next=(t.reviews||[]).filter(x=>x>=today&&!done.includes(x)).sort()[0];
    const ivl=Math.max(1,next?days(last,next):days(t.startDate||last,(t.reviews||[]).slice(-1)[0]||last)||30);
    rv.push(newReview({title:t.name,fromSched:key,created:at(t.startDate||last),S:ivl,D:clampD(FSRS_W[4]),ivl,last:at(last),
      due:next||addDays(last,ivl),lastRating:3,reps:done.length,paused:!next,log:done.map(x=>({d:x,at:at(x),r:3,ivl:0}))}))}
  for(const t of (d.todos||[])){if(!t||!t.name||t.completed)continue;const key='sched-t-'+t.id;if(seen.has(key))continue;
    tk.push(newTask({title:t.name,due:t.date||today,fromSched:key}))}
  const memo=(d.memo||'').trim();if(memo&&!seen.has('sched-memo'))mm.push({id:'m-'+nid(),text:memo,at:Date.now(),ctx:'学習スケジューラーから',fromSched:'sched-memo'});
  return {rv,tk,mm}}
async function importSched(){const d=await loadSched();
  if(!d){toast(PomoCloud.user?'学習スケジューラーのデータが見つかりませんでした':'学習スケジューラーのデータが見つかりません。同じ Google アカウントでログインしてから試してください');return}
  const p=schedPlan(d),on=p.rv.filter(x=>!x.paused).length;
  if(!p.rv.length&&!p.tk.length&&!p.mm.length){toast('引き継ぐものはありません（すべて取り込み済みです）');return}
  confirmBox(`学習スケジューラーから取り込みます。\\n・復習 ${p.rv.length}件（予定あり ${on}件／予定が終わったもの ${p.rv.length-on}件は一時停止で保存）\\n・未完了のタスク ${p.tk.length}件\\n・メモ ${p.mm.length}件\\n学習時間の記録・連続日数は引き継がれません。`,'取り込む',()=>{
    st.reviews.push(...p.rv);st.tasks.push(...p.tk);st.memos.push(...p.mm);save();renderView();toast(`取り込みました（復習 ${p.rv.length}・タスク ${p.tk.length}・メモ ${p.mm.length}）`)})}""")

# ---- account (Google login) UX ----
rep('<div class="sync" id="sync"><b></b><span id="syncText">この端末に保存</span></div>',
    '<div class="sync" id="sync"><svg class="sync-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19a4.5 4.5 0 1 0-1.4-8.8A6 6 0 0 0 4.3 12.5 3.5 3.5 0 0 0 6.5 19z"/></svg><b></b><span id="syncText">この端末に保存</span></div>')
rep('.sync.on b{background:var(--tree)} .sync.err b{background:var(--pri1)}', """.sync.on b{background:var(--tree)} .sync.err b{background:var(--pri1)}
.sync-ic{display:none;width:17px;height:17px;flex:none}
.sync.tap{display:flex!important;cursor:pointer;padding:4px 10px;border-radius:999px;position:relative}.sync.tap:hover,.sync.tap[aria-expanded="true"]{background:var(--surface);color:var(--fg);box-shadow:0 0 0 1px var(--line)}.sync.login b{background:var(--focus)}
@media(max-width:1000px){.sync.tap{padding:0;width:34px;height:34px;justify-content:center;border-radius:10px;flex:none}.sync.tap .sync-ic{display:block}.sync.tap #syncText{display:none!important}.sync.tap b{position:absolute;right:4px;top:5px;box-shadow:0 0 0 2px var(--bg)}
  .sync.tap.login{width:auto;padding:0 9px;color:var(--fg);box-shadow:0 0 0 1px var(--line);background:var(--surface)}.sync.tap.login b,.sync.tap.login .sync-ic{display:none}.sync.tap.login::after{content:"ログイン";font-size:12.5px;font-weight:600}}
@media(max-width:440px){.brand{font-size:16px;gap:6px}.topin{gap:6px!important}.topin .gear{width:30px}
  .sync.tap.login{width:34px;padding:0;color:var(--focus)}.sync.tap.login::after{content:none}.sync.tap.login .sync-ic{display:block}.sync.tap.login b{display:block;background:var(--focus);animation:pulse 1.6s ease-in-out infinite}}
.acct{position:fixed;z-index:50;top:calc(62px + env(safe-area-inset-top,0px));right:max(12px,env(safe-area-inset-right,0px));width:min(330px,calc(100% - 24px));background:var(--surface);border:1px solid var(--line);border-radius:16px;box-shadow:0 18px 40px -16px rgba(0,0,0,.35);padding:14px;display:flex;flex-direction:column;gap:10px}
.acct .who{display:flex;align-items:center;gap:10px;min-width:0}
.acct .av{width:38px;height:38px;border-radius:50%;flex:none;background:var(--sunk);display:grid;place-items:center;font-weight:700;overflow:hidden}.acct .av img{width:100%;height:100%;object-fit:cover}
.acct .who div{min-width:0}.acct .who b{display:block;font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.acct .who small{display:block;font-size:12px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.acct .stl{display:flex;align-items:center;gap:7px;font-size:12.5px;color:var(--muted);background:var(--sunk);border-radius:10px;padding:7px 10px}.acct .stl b{width:8px;height:8px;border-radius:50%;background:var(--muted);flex:none}.acct .stl.on b{background:var(--tree)}.acct .stl.err b{background:var(--pri1)}
.acct .ocopts button{padding:8px 12px}.acct a{font-size:12px;color:var(--muted);text-align:center}
.acctdlg .box{max-width:440px}.acctdlg h3{font-family:var(--display);margin:0;font-size:18px}""")
rep('<div class="modal" id="modal" hidden>', '<div class="acct" id="acct" hidden role="dialog" aria-label="アカウント"></div><div class="modal acctdlg" id="acctDlg" hidden><div class="box"><h3 id="adTitle"></h3><p id="adMsg"></p><div class="ocopts" id="adOpts"></div></div></div><div class="modal" id="modal" hidden>')

# Sync: attach / detach / flush pending writes before sign-out
rep("""const Sync={col:null,ready:false,pend:{},busy:{},stateTimer:null,first:true,""","""const Sync={col:null,ready:false,pend:{},busy:{},stateTimer:null,first:true,unsub:null,
  attach(u){this.col=PomoCloud.col(u.uid);this.set('','同期中…');LS.set('cloudUid',u.uid);
    this.unsub=this.col.onSnapshot(snap=>this.onSnap(snap),err=>this.set('err','同期エラー','この端末には保存されています: '+(err&&err.code||'')))},
  detach(){if(this.unsub)this.unsub();this.unsub=null;this.col=null;this.ready=false;this.first=true},
  async flushAll(){clearTimeout(this.stateTimer);if(this.col&&this.ready)this.pushStateNow();const idle=()=>!Object.keys(this.pend).length&&!Object.values(this.busy).some(Boolean);
    for(const t0=Date.now();!idle()&&Date.now()-t0<8000;)await new Promise(r=>setTimeout(r,150));return idle()},""")
rep("""  set(cls,txt,title){const el=$('#sync');el.className='sync '+cls;$('#syncText').textContent=txt;el.title=title||''},""",
"""  set(cls,txt,title){const el=$('#sync');el.className='sync '+cls+(el.classList.contains('tap')?' tap':'');$('#syncText').textContent=txt;el.title=title||'';if(!$('#acct').hidden)acctRender()},""")

# nudge to sign in after the first finished focus session (instead of on first visit)
rep("""function addSession(s){""","""function addSession(s){loginNudge(s);""")

rep("""/*@cloud*/""","""/*@cloud*/
const INAPP=/Line\\/|FBAN|FBAV|FB_IAB|Instagram|Twitter|MicroMessenger|KAKAOTALK|; wv\\)/i.test(navigator.userAgent);
const AUTH_ERR={'auth/popup-blocked':'ポップアップがブロックされました。もう一度ログインを押してください',
  'auth/network-request-failed':'通信できませんでした。電波のよい場所でもう一度お試しください',
  'auth/too-many-requests':'しばらく時間をおいてからお試しください',
  'auth/internal-error':'ログインに失敗しました。もう一度お試しください',
  'auth/web-storage-unsupported':'このブラウザの設定ではログインできません。Cookie を許可するか、別のブラウザでお試しください',
  'auth/unauthorized-domain':'このアドレスでのログインがまだ許可されていません（管理者：Firebase の承認済みドメインに追加してください）',
  'auth/operation-not-allowed':'Google ログインがまだ有効になっていません（管理者：Firebase で Google を有効にしてください）'};
const authErr=e=>AUTH_ERR[e&&e.code]||'ログインできませんでした'+(e&&e.code?'（'+e.code+'）':'');
const cloudOn=()=>!!window.PomoCloud&&!(window.claude&&window.claude.use);
function choose(title,msg,opts){return new Promise(res=>{$('#adTitle').textContent=title;$('#adMsg').textContent=msg;
  $('#adOpts').innerHTML=opts.map(([k,l,sub,cls])=>`<button data-k="${k}" class="${cls||''}">${esc(l)}${sub?`<small>${esc(sub)}</small>`:''}</button>`).join('');
  const dl=$('#acctDlg');dl.hidden=false;$('#adOpts').onclick=e=>{const b=e.target.closest('[data-k]');if(!b)return;dl.hidden=true;res(b.dataset.k)}})}
const localHasData=()=>Object.values(months).some(a=>(a||[]).some(x=>!x.del))||st.tasks.some(x=>!isSample(x))||st.books.some(x=>!isSample(x))||st.reviews.some(x=>!isSample(x));
async function cloudLogin(){if(!cloudOn())return;acctClose();
  if(INAPP){const k=await choose('ブラウザで開いてください','LINE や Instagram などのアプリの中で開いたページでは、Google の決まりでログインできません。\\n右上（または右下）のメニューから「ブラウザで開く」を選ぶか、アドレスをコピーして Safari や Chrome で開いてください。',[['copy','アドレスをコピー',location.origin+location.pathname],['close','閉じる']]);
    if(k==='copy'){try{await navigator.clipboard.writeText(location.origin+location.pathname);toast('コピーしました。Safari や Chrome に貼り付けて開いてください')}catch(e){toast(location.origin+location.pathname)}}return}
  let u;try{u=await PomoCloud.signIn()}catch(e){if(e&&(e.code==='auth/popup-closed-by-user'||e.code==='auth/cancelled-popup-request'||e.code==='auth/user-cancelled'))return;toast(authErr(e));return}
  if(LS.get('cloudUid',null)!==u.uid&&localHasData()){let cloud=false;try{cloud=await PomoCloud.hasCloud(u.uid)}catch(e){}
    if(cloud){const k=await choose('この端末の記録をどうしますか？',`${u.email||'このアカウント'} には、ほかの端末で保存した記録があります。この端末にも記録があります。`,
      [['merge','両方の記録をまとめる','この端末の記録をアカウントに合わせて保存します'],['cloud','アカウントの記録だけを使う','この端末の記録は使わず、アカウントの記録に置き換えます'],['cancel','ログインをやめる','この端末だけで使い続けます']]);
      if(k==='cancel'){await PomoCloud.signOut();return}
      if(k==='cloud'){st.updatedAt=0;months={};dataVer++}}}
  Sync.attach(u);toast(`${u.email||''} でログインしました`);renderView()}
function loginNudge(s){if(!cloudOn()||Sync.col||LS.get('loginHint',false)||s.k==='b'||!s.ok||s.manual)return;LS.set('loginHint',true);
  setTimeout(()=>toast('おつかれさまでした。この記録をスマホやPCでも見られるようにしませんか？','Google でログイン',cloudLogin),1800)}
async function signOutClear(after){Sync.detach();await PomoCloud.signOut();for(const k of Object.keys(localStorage))if(k.startsWith('pf2_'))localStorage.removeItem(k);if(after)try{sessionStorage.setItem('pomoAfter',after)}catch(e){}location.reload()}
function cloudLogout(after){acctClose();confirmBox(`${after==='login'?'別のアカウントに切り替えます。':'ログアウトしますか？'}\\n・この端末に保存された Pomo Timer のデータは消去されます（アカウントには残ります）\\n・同じアドレスの学習スケジューラーからもログアウトされます`,after==='login'?'切り替える':'ログアウト',async()=>{
  toast('保存しています…');if(await Sync.flushAll()){signOutClear(after);return}
  confirmBox('まだ送信できていない記録があります。今ログアウトすると、その分が失われる可能性があります。\\n通信できる場所でもう一度お試しください。','それでもログアウト',()=>signOutClear(after))})}
function cloudDelete(){const u=PomoCloud.user;if(!u)return;acctClose();
  confirmBox(`${u.email||''} の Pomo Timer のデータをクラウドからすべて削除し、ログアウトします。\\n・この端末のデータは残ります（このまま端末だけで使えます）\\n・学習スケジューラーのデータは削除されません\\n元に戻せません。`,'削除する',async()=>{
    Sync.detach();try{await PomoCloud.deleteCloud(u.uid)}catch(e){toast('削除できませんでした（'+(e&&e.code||'')+'）');Sync.attach(u);return}
    LS.set('cloudUid',null);await PomoCloud.signOut();Sync.set('login','この端末に保存 · ログイン','押すと Google でログインし、端末間で同期します');toast('クラウドのデータを削除しました')})}
function acctRender(){const u=PomoCloud.user,el=$('#acct');if(!u){acctClose();return}const sy=$('#sync');
  const st0=sy.classList.contains('on')?'on':sy.classList.contains('err')?'err':'',nm=u.displayName||u.email||'';
  el.innerHTML=`<div class="who"><span class="av">${u.photoURL?`<img src="${esc(u.photoURL)}" alt="" referrerpolicy="no-referrer">`:esc([...nm][0]||'?')}</span><div><b>${esc(nm)}</b><small>${esc(u.email||'')}</small></div></div>
  <div class="stl ${st0}"><b></b><span>${esc($('#syncText').textContent)}${st0==='on'?' · このアカウントの端末どうしで自動同期':''}</span></div>
  <div class="ocopts"><button data-a="sched">学習スケジューラーから引き継ぐ<small>復習の予定・ToDo・メモを取り込む</small></button>
  <button data-a="switch">別のアカウントに切り替え</button><button data-a="logout">ログアウト</button>
  <button data-a="fb">ご意見・要望を送る<small>ほしい機能や使いにくいところを教えてください</small></button>
  <button data-a="delete" class="danger">クラウドのデータを削除</button></div><a href="privacy.html" target="_blank" rel="noopener">データの扱いについて</a>`}
function acctOpen(){acctRender();$('#acct').hidden=false;$('#sync').setAttribute('aria-expanded','true')}
function acctClose(){const el=$('#acct');if(el)el.hidden=true;const sy=$('#sync');if(sy)sy.setAttribute('aria-expanded','false')}
if(cloudOn()){const sy=$('#sync');sy.classList.add('tap');sy.setAttribute('role','button');sy.tabIndex=0;sy.setAttribute('aria-expanded','false');
  const act=()=>{if(!PomoCloud.user||!Sync.col){cloudLogin();return}$('#acct').hidden?acctOpen():acctClose()};
  sy.addEventListener('click',e=>{e.stopPropagation();act()});sy.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();act()}});
  $('#acct').addEventListener('click',e=>{e.stopPropagation();const b=e.target.closest('[data-a]');if(!b)return;const a=b.dataset.a;
    if(a==='sched'){acctClose();importSched()}else if(a==='fb'){acctClose();fbOpen()}else if(a==='switch')cloudLogout('login');else if(a==='logout')cloudLogout();else if(a==='delete')cloudDelete()});
  document.addEventListener('click',()=>{if(!$('#acct').hidden)acctClose()});document.addEventListener('keydown',e=>{if(e.key==='Escape')acctClose()});
  let after=null;try{after=sessionStorage.getItem('pomoAfter');sessionStorage.removeItem('pomoAfter')}catch(e){}
  if(after==='login')setTimeout(()=>toast('切り替えるアカウントでログインしてください','Google でログイン',cloudLogin),800)}""")

# feedback: form -> Firestore feedback/{id} (create-only) -> GitHub Issues via .github/workflows/feedback.yml
rep('<div class="modal" id="modal" hidden>','<div class="modal fbdlg" id="fbDlg" hidden><div class="box"><h3>ご意見・要望を送る</h3><p class="muted" style="font-size:13px">「こんな機能がほしい」「ここが使いにくい」など、なんでも送ってください。今後の改善の参考にします。お名前や連絡先などの個人情報は書かないでください。</p><div class="seg" id="fbKind"><button data-k="idea" aria-pressed="true">要望</button><button data-k="bug" aria-pressed="false">不具合</button><button data-k="other" aria-pressed="false">その他</button></div><textarea id="fbText" rows="6" maxlength="2000" placeholder="例：タスクを並べ替えられるようにしてほしい"></textarea><small class="muted" id="fbCount" style="text-align:right">0 / 2000</small><div class="acts"><button class="btn" id="fbNo">やめる</button><button class="btn primary" id="fbYes">送る</button></div></div></div><div class="modal" id="modal" hidden>')
rep('.acctdlg .box{max-width:440px}','.fbdlg .box{max-width:480px}.fbdlg h3{font-family:var(--display);margin:0;font-size:18px}.fbdlg textarea{min-height:130px}\n.acctdlg .box{max-width:440px}')
# feedback card at the very bottom of the settings page (below all panels, full width)
rep('<div class="pgrid" id="prefs"></div></section>','<div class="pgrid" id="prefs"></div><div class="panel fbfoot" id="fbFoot" hidden><div><b>ご意見・要望を送る</b><small>ほしい機能や使いにくいところを教えてください。今後の改善の参考にします</small></div><button class="btn accent" id="d_fb">送る</button></div></section>')
rep('.acctdlg .box{max-width:440px}','.fbfoot{max-width:1180px;margin-top:14px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.fbfoot b{display:block;font-size:15px}.fbfoot small{display:block;color:var(--muted);font-size:12.5px}\n.acctdlg .box{max-width:440px}')
rep("""/*@cloud*/""","""/*@cloud*/
if(window.PomoCloud&&!(window.claude&&window.claude.use)){$('#fbFoot').hidden=false;$('#d_fb').onclick=()=>fbOpen()}
function fbOpen(){const d=$('#fbDlg');d.hidden=false;const ta=$('#fbText');$('#fbCount').textContent=[...ta.value].length+' / 2000';setTimeout(()=>ta.focus(),50)}
$('#fbKind').onclick=e=>{const b=e.target.closest('[data-k]');if(!b)return;$$('#fbKind button').forEach(x=>x.setAttribute('aria-pressed',x===b))};
$('#fbText').oninput=e=>{$('#fbCount').textContent=[...e.target.value].length+' / 2000'};
$('#fbNo').onclick=()=>{$('#fbDlg').hidden=true};$('#fbDlg').onclick=e=>{if(e.target.id==='fbDlg')$('#fbDlg').hidden=true};
$('#fbYes').onclick=async()=>{const text=$('#fbText').value.trim();if(!text){toast('内容を入力してください');return}
  const last=LS.get('fbAt',0);if(Date.now()-last<60000){toast('続けて送るときは少し時間をおいてください');return}
  const kind=($('#fbKind [aria-pressed="true"]')||{}).dataset?.k||'idea',btn=$('#fbYes');btn.disabled=true;btn.textContent='送信中…';
  try{await Promise.race([PomoCloud.sendFeedback({text:text.slice(0,2000),kind,page:'pomo',ua:navigator.userAgent.slice(0,300)}),new Promise((_,rj)=>setTimeout(()=>rj({code:'timeout'}),12000))]);
    LS.set('fbAt',Date.now());$('#fbText').value='';$('#fbDlg').hidden=true;toast('送信しました。ありがとうございます！')}
  catch(e){toast(e&&e.code==='timeout'?'送信できませんでした。通信できる場所でもう一度お試しください':'送信できませんでした（'+(e&&e.code||'')+'）')}
  finally{btn.disabled=false;btn.textContent='送る'}};""")

# theme color -> icons (head script window.pomoIcon) + note about installed icon
rep("function applyTheme(){document.body.dataset.accent=S.accent||'tomato';","function applyTheme(){document.body.dataset.accent=S.accent||'tomato';if(window.pomoIcon)pomoIcon(S.accent||'tomato');")
rep('<div class="pr"><span>テーマカラー</span>','<div class="pr"><span>テーマカラー<small>アプリのアイコンもこの色になります（インストール済みの場合、変わるまで時間がかかるか、入れ直しが必要です）</small></span>')
# sync: per-field timestamps (st.fu) for top-level values such as pet / settings, so a device that saves before
# receiving newer cloud data no longer reverts fields it did not touch (whole-state "newer wins" lost the chosen pet)
rep("""const SCOLS=['subjects','books','tasks','goals','alarms','reviews','memos'],PCOLS=['events','routines'];let lastSnap=null;""",
    """const SCOLS=['subjects','books','tasks','goals','alarms','reviews','memos'],PCOLS=['events','routines'];let lastSnap=null;
const TOPSKIP=new Set([...SCOLS,'plan','daily','tomb','fu','updatedAt','v']);let lastTop=null;""")
rep("""r[c]=m}lastSnap=r}""","""r[c]=m}lastSnap=r;lastTop={};for(const k in st)if(!TOPSKIP.has(k))lastTop[k]=JSON.stringify(st[k])}""")
rep("""    for(const id of prev.keys())if(!seen.has(id))st.tomb[id]=now}""","""    for(const id of prev.keys())if(!seen.has(id))st.tomb[id]=now}
  st.fu=st.fu||{};for(const k of new Set([...Object.keys(st),...Object.keys(lastTop||{})]))if(!TOPSKIP.has(k)&&lastTop&&lastTop[k]!==JSON.stringify(st[k]))st.fu[k]=now;""")
rep("""  M.tomb=tomb;M.updatedAt=Math.max(L.updatedAt||0,R.updatedAt||0);return {M,dirty}}""",
"""  {const fl=L.fu||{},fr=R.fu||{};M.fu=Object.assign({},fr);for(const k in fl)M.fu[k]=Math.max(fl[k]||0,fr[k]||0);
    for(const k of new Set([...Object.keys(L),...Object.keys(R)])){if(TOPSKIP.has(k))continue;const a=fl[k]||0,b=fr[k]||0;if(a===b)continue;const src=a>b?L:R;
      if(src[k]===undefined)delete M[k];else M[k]=JSON.parse(JSON.stringify(src[k]));if(JSON.stringify(M[k])!==JSON.stringify(R[k]))dirty=true}
    if(JSON.stringify(M.fu)!==JSON.stringify(fr))dirty=true}
  M.tomb=tomb;M.updatedAt=Math.max(L.updatedAt||0,R.updatedAt||0);return {M,dirty}}""")

open(dst, 'w', encoding='utf-8').write(h)
print('ok', len(h))
