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
  const auth=firebase.auth(),fs=firebase.firestore();auth.languageCode='ja';
  const ready=new Promise(res=>{const off=auth.onAuthStateChanged(u=>{off();res(u)})});
  return {
    ready,
    get user(){return auth.currentUser},
    col(uid){return fs.collection('pomo/'+uid+'/docs')},
    async schedDoc(uid){const d=await fs.doc('users/'+uid).get();return d.exists?d.data():null},
    async signIn(){const p=new firebase.auth.GoogleAuthProvider();p.setCustomParameters({prompt:'select_account'});return (await auth.signInWithPopup(p)).user},
    async emailSignIn(e,pw){return (await auth.signInWithEmailAndPassword(e,pw)).user},
    async emailSignUp(e,pw){const u=(await auth.createUserWithEmailAndPassword(e,pw)).user;try{await u.sendEmailVerification()}catch(x){}return u},
    resetPw(e){return auth.sendPasswordResetEmail(e)},
    sendVerify(){return auth.currentUser.sendEmailVerification()},
    async linkGoogle(){const p=new firebase.auth.GoogleAuthProvider();p.setCustomParameters({prompt:'select_account'});return (await auth.currentUser.linkWithPopup(p)).user},
    async linkPassword(pw){const u=auth.currentUser;return (await u.linkWithCredential(firebase.auth.EmailAuthProvider.credential(u.email,pw))).user},
    providers(){return ((auth.currentUser&&auth.currentUser.providerData)||[]).map(p=>p.providerId)},
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
      if(!u){this.set('login','この端末に保存 · ログイン','押すとログインし、端末間で同期します');return}
      this.attach(u);return}""")

# 3. settings row: account status + login / logout
rep("""<div class="pr"><span>同期<small>${Sync.col?'同じアカウントで開いた端末どうしで自動同期しています':'この端末のブラウザに保存中。claude.ai にサインインして開くと同期されます'}</small></span></div>""",
"""<div class="pr"><span>同期<small>${Sync.col?(window.PomoCloud&&PomoCloud.user?esc(PomoCloud.user.email||'')+' でログイン中。同じアカウントの端末どうしで自動同期しています':'同じアカウントで開いた端末どうしで自動同期しています'):(window.PomoCloud?'この端末のブラウザに保存中。ログインすると端末間で同期されます':'この端末のブラウザに保存中。claude.ai にサインインして開くと同期されます')}</small></span>${window.PomoCloud?(PomoCloud.user?'<button class="btn" id="d_logout">ログアウト</button>':'<button class="btn accent" id="d_login">ログイン</button>'):''}</div>""")

# 4. handlers
rep("""  if(t.id==='d_export')exportData();if(t.id==='d_import')$('#importFile').click();""",
"""  if(t.id==='d_export')exportData();if(t.id==='d_import')$('#importFile').click();
  if(t.id==='d_login'){cloudLogin();return}
  if(t.id==='d_logout'){cloudLogout();return}""")

rep("""async function saveFile(name,data){""",
"""if(window.PomoCloud&&new URLSearchParams(location.search).get('import')==='sched'){history.replaceState(null,'',location.pathname);PomoCloud.ready.then(()=>setTimeout(()=>importSched(true),1200))}
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
async function importSched(auto){
  const k=auto?'here':await choose('学習スケジューラーから引き継ぐ','どこから取り込みますか？',[['here','このブラウザ・ログイン中のアカウントから','学習スケジューラーを同じブラウザで使っていたか、同じ Google アカウントでログインしている場合'],['file','書き出したファイルから','学習スケジューラーの「📤 書き出し」で保存したファイル（別の端末・別のログイン方法でも使えます）'],['cancel','やめる']]);
  if(k==='cancel')return;if(k==='file'){$('#schedFile').click();return}
  const d=await loadSched();
  if(!d){toast(PomoCloud.user?'学習スケジューラーのデータが見つかりませんでした。「書き出したファイルから」もお試しください':'学習スケジューラーのデータが見つかりません。学習スケジューラーの「📤 書き出し」で保存したファイルから取り込めます');return}
  importSchedData(d)}
function importSchedData(d){
  if(!d||(!Array.isArray(d.tasks)&&!Array.isArray(d.todos)&&!d.memo)){toast('学習スケジューラーのファイルではないようです');return}
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
.acctdlg .box{max-width:440px}.acctdlg h3{font-family:var(--display);margin:0;font-size:18px}
.logindlg .box{max-width:400px}.logindlg h3{font-family:var(--display);margin:0;font-size:19px}.logindlg form{display:flex;flex-direction:column;gap:10px}.logindlg #lgSubmit{padding:10px}
.gbtn{width:100%;padding:10px;gap:10px;font-weight:600}.lgor{display:flex;align-items:center;gap:10px;font-size:12px;color:var(--muted);margin:14px 0 4px}.lgor::before,.lgor::after{content:"";flex:1;border-top:1px solid var(--line)}
.lgnote{font-size:12.5px;color:var(--muted);margin:0;background:var(--sunk);padding:8px 10px;border-radius:10px}.lgerr{margin:0;color:var(--pri1);font-size:13px}
.lglinks{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}.lglink{background:none;border:0;padding:0;font:inherit;font-size:12.5px;color:var(--muted);text-decoration:underline;cursor:pointer}""")
rep('<div class="modal" id="modal" hidden>', '<div class="modal logindlg" id="loginDlg" hidden><div class="box" role="dialog" aria-labelledby="lgTitle"><h3 id="lgTitle">ログイン</h3><div id="lgGoogleWrap"><button type="button" class="btn gbtn" id="lgGoogle"><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.4h6.5a5.6 5.6 0 0 1-2.4 3.6v3h3.9c2.3-2.1 3.5-5.2 3.5-8.7z"/><path fill="#34A853" d="M12 24c3.2 0 6-1.1 8-2.9l-3.9-3c-1.1.7-2.5 1.2-4.1 1.2-3.1 0-5.8-2.1-6.7-5H1.3v3.1A12 12 0 0 0 12 24z"/><path fill="#FBBC05" d="M5.3 14.3a7.2 7.2 0 0 1 0-4.6V6.6H1.3a12 12 0 0 0 0 10.8z"/><path fill="#EA4335" d="M12 4.8c1.8 0 3.3.6 4.6 1.8l3.4-3.4A12 12 0 0 0 1.3 6.6l4 3.1c.9-2.9 3.6-4.9 6.7-4.9z"/></svg>Google でログイン</button><p class="lgnote" id="lgInapp" hidden>このアプリの中で開いたページでは Google ログインが使えません。下のメールアドレスでログインするか、<button type="button" class="lglink" id="lgCopy">アドレスをコピー</button>して Safari や Chrome で開いてください。</p><div class="lgor"><span>または メールアドレスで</span></div></div><form id="lgForm" novalidate><label class="f">メールアドレス<input type="email" id="lgEmail" autocomplete="email" inputmode="email"></label><label class="f">パスワード<input type="password" id="lgPw" autocomplete="current-password"></label><small class="muted" id="lgHint" hidden>6文字以上。ほかのサービスと同じパスワードは避けてください</small><p class="lgerr" id="lgErr" role="alert" hidden></p><button class="btn primary" id="lgSubmit">ログイン</button></form><div class="lglinks"><button type="button" class="lglink" id="lgMode">はじめての方は新規登録</button><button type="button" class="lglink" id="lgForgot">パスワードを忘れた</button></div><div class="acts"><button type="button" class="btn" id="lgClose">閉じる</button></div></div></div><div class="acct" id="acct" hidden role="dialog" aria-label="アカウント"></div><div class="modal acctdlg" id="acctDlg" hidden><div class="box"><h3 id="adTitle"></h3><p id="adMsg"></p><div class="ocopts" id="adOpts"></div></div></div><div class="modal" id="modal" hidden>')

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
  'auth/operation-not-allowed':'このログイン方法はまだ有効になっていません（管理者：Firebase の Sign-in method で有効にしてください）',
  'auth/invalid-email':'メールアドレスの形が正しくありません','auth/missing-email':'メールアドレスを入力してください',
  'auth/weak-password':'パスワードは6文字以上にしてください','auth/missing-password':'パスワードを入力してください',
  'auth/email-already-in-use':'このメールアドレスはすでに登録されています。「ログイン」からお試しください',
  'auth/wrong-password':'メールアドレスかパスワードが違います','auth/user-not-found':'メールアドレスかパスワードが違います',
  'auth/invalid-credential':'メールアドレスかパスワードが違います','auth/invalid-login-credentials':'メールアドレスかパスワードが違います',
  'auth/user-disabled':'このアカウントは使えなくなっています',
  'auth/account-exists-with-different-credential':'このメールアドレスは別の方法で登録されています。その方法でログインしてから、アカウントのメニューでログイン方法を追加してください',
  'auth/credential-already-in-use':'このログイン方法は、別のアカウントですでに使われています',
  'auth/provider-already-linked':'このログイン方法はすでに追加されています',
  'auth/requires-recent-login':'安全のため、一度ログアウトしてログインし直してから、もう一度お試しください'};
const authErr=e=>AUTH_ERR[e&&e.code]||'ログインできませんでした'+(e&&e.code?'（'+e.code+'）':'');
const cloudOn=()=>!!window.PomoCloud&&!(window.claude&&window.claude.use);
function choose(title,msg,opts){return new Promise(res=>{$('#adTitle').textContent=title;$('#adMsg').textContent=msg;
  $('#adOpts').innerHTML=opts.map(([k,l,sub,cls])=>`<button data-k="${k}" class="${cls||''}">${esc(l)}${sub?`<small>${esc(sub)}</small>`:''}</button>`).join('');
  const dl=$('#acctDlg');dl.hidden=false;$('#adOpts').onclick=e=>{const b=e.target.closest('[data-k]');if(!b)return;dl.hidden=true;res(b.dataset.k)}})}
const localHasData=()=>Object.values(months).some(a=>(a||[]).some(x=>!x.del))||st.tasks.some(x=>!isSample(x))||st.books.some(x=>!isSample(x))||st.reviews.some(x=>!isSample(x));
let lgMode='in';
function cloudLogin(){if(!cloudOn())return;acctClose();loginOpen('in')}
function loginOpen(mode){lgMode=mode;const link=mode==='link',u=PomoCloud.user;
  $('#lgTitle').textContent=link?'パスワードでのログインを追加':mode==='up'?'新規登録':'ログイン';
  $('#lgGoogleWrap').hidden=link;$('#lgGoogle').hidden=INAPP;$('#lgInapp').hidden=!INAPP||link;
  $('#lgEmail').readOnly=link;if(link)$('#lgEmail').value=(u&&u.email)||'';
  $('#lgPw').autocomplete=mode==='in'?'current-password':'new-password';$('#lgHint').hidden=mode==='in';
  $('#lgSubmit').textContent=link?'追加する':mode==='up'?'登録する':'ログイン';
  $('#lgMode').hidden=link;$('#lgMode').textContent=mode==='up'?'登録済みの方はログイン':'はじめての方は新規登録';$('#lgForgot').hidden=mode!=='in';
  $('#lgErr').hidden=true;$('#loginDlg').hidden=false;setTimeout(()=>(link?$('#lgPw'):$('#lgEmail')).focus(),50)}
const lgFail=e=>{$('#lgErr').textContent=authErr(e);$('#lgErr').hidden=false};
$('#lgClose').onclick=()=>$('#loginDlg').hidden=true;$('#loginDlg').onclick=e=>{if(e.target.id==='loginDlg')$('#loginDlg').hidden=true};
$('#lgMode').onclick=()=>loginOpen(lgMode==='up'?'in':'up');
$('#lgCopy').onclick=async()=>{try{await navigator.clipboard.writeText(location.origin+location.pathname);toast('コピーしました。Safari や Chrome に貼り付けて開いてください')}catch(e){toast(location.origin+location.pathname)}};
$('#lgForgot').onclick=async()=>{const em=$('#lgEmail').value.trim();if(!em){lgFail({code:'auth/missing-email'});return}
  try{await PomoCloud.resetPw(em);$('#lgErr').hidden=true;toast('パスワード再設定のメールを送りました（届かないときは迷惑メールも確認してください）')}catch(e){lgFail(e)}};
$('#lgGoogle').onclick=async()=>{$('#loginDlg').hidden=true;lgMode='in';let u;try{u=await PomoCloud.signIn()}catch(e){if(e&&(e.code==='auth/popup-closed-by-user'||e.code==='auth/cancelled-popup-request'||e.code==='auth/user-cancelled'))return;toast(authErr(e));return}afterSignIn(u)};
$('#lgForm').onsubmit=async e=>{e.preventDefault();const em=$('#lgEmail').value.trim(),pw=$('#lgPw').value,b=$('#lgSubmit');
  if(!em&&lgMode!=='link'){lgFail({code:'auth/missing-email'});return}if(!pw){lgFail({code:'auth/missing-password'});return}
  b.disabled=true;let u;
  try{u=lgMode==='link'?await PomoCloud.linkPassword(pw):lgMode==='up'?await PomoCloud.emailSignUp(em,pw):await PomoCloud.emailSignIn(em,pw)}catch(x){lgFail(x);return}finally{b.disabled=false}
  $('#lgPw').value='';$('#loginDlg').hidden=true;
  if(lgMode==='link'){toast('パスワードでもログインできるようになりました');if(!$('#acct').hidden)acctRender();return}
  if(lgMode==='up')toast('登録しました。確認メールを送ったので、メール内のリンクを開いてください');
  afterSignIn(u)};
async function afterSignIn(u){
  if(LS.get('cloudUid',null)!==u.uid&&localHasData()){let cloud=false;try{cloud=await PomoCloud.hasCloud(u.uid)}catch(e){}
    if(cloud){const k=await choose('この端末の記録をどうしますか？',`${u.email||'このアカウント'} には、ほかの端末で保存した記録があります。この端末にも記録があります。`,
      [['merge','両方の記録をまとめる','この端末の記録をアカウントに合わせて保存します'],['cloud','アカウントの記録だけを使う','この端末の記録は使わず、アカウントの記録に置き換えます'],['cancel','ログインをやめる','この端末だけで使い続けます']]);
      if(k==='cancel'){await PomoCloud.signOut();return}
      if(k==='cloud'){st.updatedAt=0;months={};dataVer++}}}
  Sync.attach(u);if(lgMode!=='up')toast(`${u.email||''} でログインしました`);renderView()}
function loginNudge(s){if(!cloudOn()||Sync.col||LS.get('loginHint',false)||s.k==='b'||!s.ok||s.manual)return;LS.set('loginHint',true);
  setTimeout(()=>toast('おつかれさまでした。この記録をスマホやPCでも見られるようにしませんか？','ログイン',cloudLogin),1800)}
async function signOutClear(after){Sync.detach();await PomoCloud.signOut();for(const k of Object.keys(localStorage))if(k.startsWith('pf2_'))localStorage.removeItem(k);if(after)try{sessionStorage.setItem('pomoAfter',after)}catch(e){}location.reload()}
function cloudLogout(after){acctClose();confirmBox(`${after==='login'?'別のアカウントに切り替えます。':'ログアウトしますか？'}\\n・この端末に保存された Pomo Timer のデータは消去されます（アカウントには残ります）\\n・同じアドレスの学習スケジューラーからもログアウトされます`,after==='login'?'切り替える':'ログアウト',async()=>{
  toast('保存しています…');if(await Sync.flushAll()){signOutClear(after);return}
  confirmBox('まだ送信できていない記録があります。今ログアウトすると、その分が失われる可能性があります。\\n通信できる場所でもう一度お試しください。','それでもログアウト',()=>signOutClear(after))})}
function cloudDelete(){const u=PomoCloud.user;if(!u)return;acctClose();
  confirmBox(`${u.email||''} の Pomo Timer のデータをクラウドからすべて削除し、ログアウトします。\\n・この端末のデータは残ります（このまま端末だけで使えます）\\n・学習スケジューラーのデータは削除されません\\n元に戻せません。`,'削除する',async()=>{
    Sync.detach();try{await PomoCloud.deleteCloud(u.uid)}catch(e){toast('削除できませんでした（'+(e&&e.code||'')+'）');Sync.attach(u);return}
    LS.set('cloudUid',null);await PomoCloud.signOut();Sync.set('login','この端末に保存 · ログイン','押すとログインし、端末間で同期します');toast('クラウドのデータを削除しました')})}
function acctRender(){const u=PomoCloud.user,el=$('#acct');if(!u){acctClose();return}const sy=$('#sync');
  const st0=sy.classList.contains('on')?'on':sy.classList.contains('err')?'err':'',nm=u.displayName||u.email||'',pv=PomoCloud.providers(),hasG=pv.includes('google.com'),hasP=pv.includes('password');
  el.innerHTML=`<div class="who"><span class="av">${u.photoURL?`<img src="${esc(u.photoURL)}" alt="" referrerpolicy="no-referrer">`:esc([...nm][0]||'?')}</span><div><b>${esc(nm)}</b><small>${esc(u.email||'')}</small></div></div>
  <div class="stl ${st0}"><b></b><span>${esc($('#syncText').textContent)}${st0==='on'?' · このアカウントの端末どうしで自動同期':''}</span></div>
  <div class="stl"><span>ログイン方法：${[hasG&&'Google',hasP&&'メールアドレス＋パスワード'].filter(Boolean).join('・')||'—'}</span></div>
  ${hasP&&!u.emailVerified?`<div class="stl err"><b></b><span>メールアドレスの確認がまだです。届いたメールのリンクを開いてください</span></div>`:''}
  <div class="ocopts">${hasP&&!u.emailVerified?'<button data-a="verify">確認メールをもう一度送る</button>':''}${!hasG?'<button data-a="addG">Google でのログインを追加<small>同じ記録に Google でも入れるようにする</small></button>':''}${!hasP&&u.email?'<button data-a="addP">パスワードでのログインを追加<small>Google が使えない端末でも入れるようにする</small></button>':''}
  <button data-a="sched">学習スケジューラーから引き継ぐ<small>復習の予定・ToDo・メモを取り込む</small></button>
  <button data-a="switch">別のアカウントに切り替え</button><button data-a="logout">ログアウト</button>
  <button data-a="fb">ご意見・要望を送る<small>ほしい機能や使いにくいところを教えてください</small></button>
  <button data-a="delete" class="danger">クラウドのデータを削除</button></div><a href="privacy.html" target="_blank" rel="noopener">データの扱いについて</a>`}
function acctOpen(){acctRender();$('#acct').hidden=false;$('#sync').setAttribute('aria-expanded','true')}
function acctClose(){const el=$('#acct');if(el)el.hidden=true;const sy=$('#sync');if(sy)sy.setAttribute('aria-expanded','false')}
if(cloudOn()){const sy=$('#sync');sy.classList.add('tap');sy.setAttribute('role','button');sy.tabIndex=0;sy.setAttribute('aria-expanded','false');
  const act=()=>{if(!PomoCloud.user||!Sync.col){cloudLogin();return}$('#acct').hidden?acctOpen():acctClose()};
  sy.addEventListener('click',e=>{e.stopPropagation();act()});sy.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();act()}});
  $('#acct').addEventListener('click',e=>{e.stopPropagation();const b=e.target.closest('[data-a]');if(!b)return;const a=b.dataset.a;
    if(a==='verify'){PomoCloud.sendVerify().then(()=>toast('確認メールを送りました'),x=>toast(authErr(x)));return}
    if(a==='addP'){acctClose();loginOpen('link');return}
    if(a==='addG'){acctClose();PomoCloud.linkGoogle().then(()=>toast('Google でもログインできるようになりました'),x=>{if(x&&/popup-closed|cancelled-popup|user-cancelled/.test(x.code||''))return;toast(authErr(x))});return}
    if(a==='sched'){acctClose();importSched()}else if(a==='fb'){acctClose();fbOpen()}else if(a==='switch')cloudLogout('login');else if(a==='logout')cloudLogout();else if(a==='delete')cloudDelete()});
  document.addEventListener('click',()=>{if(!$('#acct').hidden)acctClose()});document.addEventListener('keydown',e=>{if(e.key==='Escape')acctClose()});
  let after=null;try{after=sessionStorage.getItem('pomoAfter');sessionStorage.removeItem('pomoAfter')}catch(e){}
  if(after==='login')setTimeout(()=>toast('切り替えるアカウントでログインしてください','ログイン',cloudLogin),800)}""")

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

# scheduler export file: dedicated picker, and the backup "読み込み" also accepts it
rep('<input type="file" id="importFile" accept=".json,application/json" hidden>','<input type="file" id="importFile" accept=".json,application/json" hidden><input type="file" id="schedFile" accept=".json,application/json" hidden>')
rep("const o=JSON.parse(r.result);if(o.app!=='pomo-timer'||!o.state)throw 0;","const o=JSON.parse(r.result);if(o.app==='study-scheduler'){e.target.value='';importSchedData(o);return}if(o.app!=='pomo-timer'||!o.state)throw 0;")
rep("""/*@cloud*/""","""/*@cloud*/
$('#schedFile').onchange=e=>{const f=e.target.files[0];e.target.value='';if(!f)return;const r=new FileReader();r.onload=()=>{let o=null;try{o=JSON.parse(r.result)}catch(x){}importSchedData(o&&o.app==='study-scheduler'?o:null)};r.readAsText(f)};""")
# pet illustrations (pomo/pets/<kind>/<breed>/<stage>[_mood].webp, made by tools/pets_process.py):
# when a breed has pictures, petSVG draws them inside the same <svg class="pet"> so the existing motion keeps working
rep("function petSVG(p,lv,mood,cls){","function petSVG(p,lv,mood,cls){const _img=petImgSVG(p,lv,mood,cls);if(_img)return _img;")
rep("petSVG({kind,v},l,0)","petSVG({kind,v},l,0,'still')")
rep("el.innerHTML=petSVG(st.pet,lv,mood,s8==='cheer'?'jump':'');","el.innerHTML=petSVG(st.pet,lv,mood,s8==='cheer'?'jump':s8==='go'?'go':'');")
rep("""/*@cloud*/""","""/*@cloud*/
const PET_IMG={'dog/shiba':['0','1','2','3','4','3_happy','3_sad','3_tired','3_focus']};
function petImgSVG(p,lv,mood,cls){if(!p)return '';const have=PET_IMG[p.kind+'/'+p.v];if(!have)return '';
  const K=PETS[p.kind]||PETS.tree,V=K.v[p.v]||Object.values(K.v)[0],stage=petStage(lv);
  const want=stage===0||/\\bstill\\b/.test(cls||'')?null:/\\bgo\\b/.test(cls||'')?'focus':['happy',null,'sad','tired','tired'][mood];
  const name=want&&have.includes(stage+'_'+want)?stage+'_'+want:String(stage),sc=stage===0?.8:[1,.7,.82,.94,1][stage];
  return `<svg viewBox="0 0 200 200" class="pet m${mood} ${cls||''}" role="img" aria-label="${esc(K.n+'・'+V[0]+'・'+K.st[stage]+'・'+(MOOD[mood]?MOOD[mood][0]:'おやすみ'))}"><ellipse cx="100" cy="189" rx="${52*sc}" ry="6" fill="#000" opacity=".1"/>
    <g class="pbody"><image href="pets/${p.kind}/${p.v}/${name}.webp" x="0" y="5" width="200" height="200" preserveAspectRatio="xMidYMid meet"/></g></svg>`}""")

# focus pause allowance: total pause per focus session is limited (default 3 min); past it the timer resumes by itself
rep("const DEF={calGroup:","const DEF={pauseMax:3,calGroup:")
rep("selKeys=['theme',","selKeys=['pauseMax','theme',")
rep('<label class="pr"><span>離席を記録<small>','<label class="pr"><span>集中中の一時停止<small>1回の集中で一時停止できる合計時間。過ぎると自動で再開します</small></span>${sel(\'p_pauseMax\',{0:\'しない\',1:\'1分まで\',3:\'3分まで\',5:\'5分まで\',none:\'制限なし\'},S.pauseMax??3)}</label>\n    <label class="pr"><span>離席を記録<small>')
rep("function start(force){audio();if(T.running)return;","function start(force){audio();if(T.running)return;if(T.pausedAt){T.pauseUsed=(T.pauseUsed||0)+(Date.now()-T.pausedAt)/1000;T.pausedAt=0}")
rep("if(T.mode==='focus'&&!T.startedAt){T.brkFrom=0;","if(T.mode==='focus'&&!T.startedAt){T.pauseUsed=0;T.pausedAt=0;T.brkFrom=0;")
rep("T.running?pause():start()","T.running?userPause():start()",4)
rep("if(T.running)pause();else start(true)","if(T.running)userPause();else start(true)")
rep("""/*@cloud*/""","""/*@cloud*/
function pauseLeft(){const m=S.pauseMax??3;if(m==='none'||T.mode!=='focus'||!T.startedAt)return Infinity;return m*60-(T.pauseUsed||0)}
function userPause(){const left=pauseLeft();
  if(left<=0){toast((S.pauseMax??3)===0?'集中中は一時停止できない設定です（設定 > 集中中の一時停止）':'この集中では、一時停止できる時間を使い切りました');return}
  pause();if(isFinite(left)){T.pausedAt=Date.now();persistT();toast(`一時停止中。あと ${fmt(left)} で自動的に再開します`)}}
setInterval(()=>{const m=S.pauseMax??3;if(T.running||!T.pausedAt||m==='none'||T.mode!=='focus'||!T.startedAt)return;
  if((T.pauseUsed||0)+(Date.now()-T.pausedAt)/1000>=m*60){start(true);toast('一時停止できる時間を過ぎたので、集中を再開しました')}},1000);""")

# leaving the app during focus: past the chosen limit (default 45 s) the focus fails (recorded as abandoned, timer reset)
rep("const DEF={pauseMax:3,","const DEF={leavePen:45,pauseMax:3,")
rep("selKeys=['pauseMax',","selKeys=['leavePen','pauseMax',")
rep("${swc('p_strict',S.strict)}</label>","${swc('p_strict',S.strict)}</label>\n    <label class=\"pr\"><span>離れたときのペナルティ<small>集中中にこの時間以上アプリを離れると、その集中は失敗になります（画面を消した場合も含む）</small></span>${sel('p_leavePen',{off:'記録だけ',60:'60秒で失敗',45:'45秒で失敗',30:'30秒で失敗',10:'10秒で失敗',0:'すぐ失敗'},S.leavePen??45)}</label>")
rep("else{if(T.running)lockWake();if(T.leftAt&&T.running&&T.mode==='focus'&&S.strict){toast(`集中中にこの画面を離れました（${T.int}回目）`);T.leftAt=0}renderTimer()}});",
    "else{if(T.running)lockWake();if(T.leftAt&&T.running&&T.mode==='focus'&&S.strict){if(leaveCheck())return;const L=S.leavePen??45;toast(`集中中にこの画面を離れました（${T.int}回目）${L==='off'?'':`。${L}秒以上離れると失敗になります`}`);T.leftAt=0}renderTimer()}});")
rep("""/*@cloud*/""","""/*@cloud*/
function failFocus(away){const ss=segSec();pause();
  if(T.mode==='focus'&&T.startedAt&&ss>=60){const s=recordSession(false,ss);T.brkPend=s.id}
  T.startedAt=0;T.segOff=0;T.segStart=0;T.contId=null;if(T.contPrev)endCont();
  T.remaining=T.total=durFor(T.mode);T.elapsed=0;T.int=0;T.noticed=false;T.leftAt=0;T.pausedAt=0;persistT();renderAll();
  toast(`${away>=120?Math.round(away/60)+'分':away+'秒'}離れたので、この集中は失敗になりました${ss>=60?'（森に枯れ木が1本）':''}`)}
function leaveCheck(){const L=S.leavePen??45;if(L==='off'||!S.strict||!T.leftAt||!T.running||T.mode!=='focus'||!T.startedAt)return false;
  const away=Math.round((Date.now()-T.leftAt)/1000);if(away<+L||away<1)return false;failFocus(away);return true}
setTimeout(leaveCheck,300); // the app was closed during a focus and opened again later""")

# calendar: group a day's plans by type when it has 4 or more (feedback #9); users who already chose keep their choice
rep("calGroup:'none',calGroupMin:4","calGroup:'type',calGroupMin:4")
# ---- feedback #20/#21/#22 ----
# A1: a book saved with goal "なし" kept getting the only open goal suggested (and linked on the next save)
rep("function autoGoal(b){if(bookGoal(b))return null;","function autoGoal(b){if(bookGoal(b)||b.noGoal)return null;")
rep("const gid=$('#bp_goal').value;st.goals.forEach(x=>{x.books=(x.books||[]).filter(y=>y!==b.id)});","const gid=$('#bp_goal').value;b.noGoal=!gid;st.goals.forEach(x=>{x.books=(x.books||[]).filter(y=>y!==b.id)});")
# A2: day counts ignored repeating plans (cell said 0件 while chips showed) and the day panel said
#     「0件」「この日の予定はありません」 while routine / tentative plans were listed below
rep("open=es.filter(e=>!e.done&&!e.proj).length","open=es.filter(e=>!e.done&&(!e.proj||e.repProj)).length")
rep("<small>${real.length+reps.length}件の予定${proj.length?`・仮 ${proj.length}`:''}","<small>${real.length+reps.length+rts.length}件の予定${proj.length?`・仮 ${proj.length}`:''}")
rep(":reps.length?'':'<div class=\"empty\" style=\"padding:10px 0\">この日の予定はありません</div>'}",":(reps.length||proj.length||rts.length||evs.length||goalsOn(k).length)?'':'<div class=\"empty\" style=\"padding:10px 0\">この日の予定はありません</div>'}")
# A3: "1日 ○" meant different things on different screens; say what each number is
rep("desc:desc+`・1日 約${Math.round(per*10)/10}${b.unit}`","desc:desc+`・学習する日1日あたり 約${Math.round(per*10)/10}${b.unit}`")
rep("desc:desc+`・1日 約${Math.round(per*10)/10}単元`","desc:desc+`・学習する日1日あたり 約${Math.round(per*10)/10}単元`")
rep("pi.pace?`最近 1日 ${uAmt(b,pi.pace)}`","pi.pace?`最近の実績 1日 ${uAmt(b,pi.pace)}`")
rep("`（1日 ${pi.need===Infinity?'—':uAmt(b,pi.need)} 必要）`","`（残り÷期限までの学習日＝1日 ${pi.need===Infinity?'—':uAmt(b,pi.need)}）`")
rep("<th>1日あたり必要</th>","<th>1日あたり必要<br><small>残り÷学習日</small></th>")
# A4: the exam template fills the stages but not the target value; point at the empty field instead of failing on save
rep("const fn=()=>{ms=ms.filter(m=>(m.t||'').trim()&&m.done).concat(tp);msDraw()};","const fn=()=>{ms=ms.filter(m=>(m.t||'').trim()&&m.done).concat(tp);msDraw();const tg=$('#g_tg');if(tg&&tg.offsetParent&&tg.value===''){tg.classList.add('needval');toast('ひな形を入れました。目標値（点数など）も入れてください');tg.focus()}};")
rep("if(mm==='yes'&&$('#g_tg').value===''){toast('目標値を入力してください（数値で測らない場合は「いいえ」）');$('#g_tg').focus();return}","if(mm==='yes'&&$('#g_tg').value===''){toast('目標値を入力してください（数値で測らない場合は「いいえ」）');$('#g_tg').classList.add('needval');$('#g_tg').focus();return}")
rep('.acctdlg .box{max-width:440px}','.needval{outline:2px solid var(--pri1);outline-offset:1px}.needval:not(:placeholder-shown){outline-color:transparent}\n.acctdlg .box{max-width:440px}')
# ---- B: clarity (feedback #21/#22) ----
# disabled "逆算" button says why (#21-6)
rep("<button class=\"btn accent\" id=\"plGen\"${bs.some(b=>b.sched)?'':' disabled'}>","${bs.some(b=>b.sched)?'':'<small class=\"muted\" style=\"display:block;font-size:12px;margin:0 0 4px\">押すには、教材の計画で「期限」か「1日の量の上限」を入れてください</small>'}<button class=\"btn accent\" id=\"plGen\"${bs.some(b=>b.sched)?'':' disabled title=\"教材の計画で期限か1日の量の上限を入れると押せます\"'}>")
# range vs total, with the unit (#22-10)
rep("aria-pressed=\"${b.mode==='amount'}\">量（15ページ）</button></div></div>","aria-pressed=\"${b.mode==='amount'}\">量（15ページ）</button></div><small class=\"muted\">範囲＝「p.10〜24」のように始めと終わりで記録（どこまで進んだかを自動で計算）。量＝「15ページ」のように進んだ量だけ記録。</small></div>")
rep('<label class="f">全体の量（任意）<input type="number" id="e_total"','<label class="f">全体の量（任意・${esc(b.unit||"ページ")}）<small class="muted">進み具合（％）と残りの計算に使います</small><input type="number" id="e_total"')
# past-paper order explains itself (#22-11)
rep('<option value="old">古い年度から</option></select></label>','<option value="old">古い年度から</option></select><small class="muted">新しい年度から＝今の出題傾向に近い順。古い年度から＝直前期に新しい年度を残せます</small></label>')
# where to edit available time from the make tab (#22-7, #22-6)
rep('<button class="chip" data-jump="pl-time">3 予定と時間</button>','<button class="chip" data-jump="pl-time">3 使える時間・予定</button>')
rep('使える時間 → 作成、と順番に進められます。</small>','使える時間 → 作成、と順番に進められます。慣れたら、下の 1〜5 を直接編集できます（曜日・使える時間は「3」）。</small>')
# "remove from plan" vs "delete the book" (#22-8)
rep("${b.sched?'<button class=\"btn danger\" id=\"bp_off\" style=\"margin-left:auto\">計画から外す</button>':''}</div></div>","${b.sched?'<button class=\"btn danger\" id=\"bp_off\" style=\"margin-left:auto\">計画から外す</button>':''}</div><small class=\"muted\">「計画から外す」は計画で作ったタスクだけを消し、教材と学習の記録は残します。教材ごと消すときは <button type=\"button\" class=\"lglink\" data-bedit=\"${b.id}\">教材の編集</button> の「削除」から。</small></div>")
# complete / move / delete side by side in task details (#21-7)
rep('<button class="btn danger" id="d_del" style="margin-left:auto">削除</button>','<button class="btn" id="d_movejump" type="button">日付を変える</button><button class="btn danger" id="d_del" style="margin-left:auto">削除</button>')
# repeat: when does it end (#21-2)
rep("<input type=\"date\" id=\"d_until\" value=\"${t.until||''}\"></label>","<input type=\"date\" id=\"d_until\" value=\"${t.until||''}\"><span class=\"chips\" style=\"margin-top:4px\">${[['1週間',7],['1か月',30],['3か月',91]].map(([n,d])=>`<button type=\"button\" class=\"chip\" data-until=\"${d}\">${n}</button>`).join('')}<button type=\"button\" class=\"chip\" data-until=\"0\">終わりなし</button></span></label>")
# planner drafts: say what confirm / undo do, and keep the bar in view (#21-4)
rep('<div class="draftbar"><b>未確定の変更 ${n}件</b>','<div class="draftbar"><b>未確定の変更 ${n}件<small style="display:block;font-weight:400;font-size:11.5px;color:var(--muted)">「確定」でカレンダーと今日のリストに反映、「取り消す」で元に戻ります</small></b>')
rep('.draftbar{','.draftbar{position:sticky;top:calc(64px + env(safe-area-inset-top,0px));z-index:6;')
# calendar "+ タスク": estimate and repeat right there (#21-5)
rep('<input class="titlein" id="na_title" placeholder="タスク（例: 書類を提出）" maxlength="140">','<input class="titlein" id="na_title" placeholder="タスク（例: 書類を提出）" maxlength="140">\n  <div class="frow"><label class="f">見積（ポモ）<input type="number" id="na_est" min="1" max="20" value="1" inputmode="numeric"></label><label class="f">繰り返し<select id="na_rep">${Object.entries(REP).map(([k,v])=>`<option value="${k}">${v}</option>`).join(\'\')}</select></label></div>\n  <label class="f" id="na_untilw" hidden>終了日（任意・空欄なら続きます）<input type="date" id="na_until"></label>')
rep("const t=parseQuick(v,'');t.title=t.title||v;if(!t.due)t.due=day;st.tasks.push(t);","const t=parseQuick(v,'');t.title=t.title||v;if(!t.due)t.due=day;{const es=+$('#na_est').value,rp=$('#na_rep').value,un=$('#na_until').value;if(es>0&&!/\\*\\d/.test(v))t.est=es;if(rp!=='none'&&(!t.repeat||t.repeat==='none'))t.repeat=rp;if(t.repeat&&t.repeat!=='none'&&un)t.until=un}st.tasks.push(t);")
rep("""/*@cloud*/""","""/*@cloud*/
document.addEventListener('click',e=>{const t=e.target;
  const be=t.closest('[data-bedit]');if(be){closeDrawer();setTimeout(()=>editBook(be.dataset.bedit),60);return}
  if(t.id==='d_movejump'){const i=$('#d_due');if(i){i.scrollIntoView({block:'center',behavior:'smooth'});i.focus();try{i.showPicker&&i.showPicker()}catch(x){}}return}
  const u=t.closest('[data-until]');if(u){e.preventDefault();const i=$('#d_until');if(!i)return;i.value=+u.dataset.until?addDays(todayKey(),+u.dataset.until):'';i.dispatchEvent(new Event('change',{bubbles:true}));toast(+u.dataset.until?`${shortDay(i.value)}までで止めます`:'終わりなしで繰り返します');return}});
document.addEventListener('change',e=>{const t=e.target;
  if(t.id==='na_rep'){const w=$('#na_untilw');if(w)w.hidden=t.value==='none'}
  if(t.id==='d_rep2'&&t.value!=='none')setTimeout(()=>toast('「終了日」でいつまで繰り返すか決められます（空欄なら続きます）'),300)});
// folded "細かい設定" shows what it currently holds (#22-9)
function bpAdvSum(){const d=$('#bp_adv');if(!d)return;const s=d.querySelector('summary');let el=s.querySelector('.advsum');if(!el){el=document.createElement('small');el.className='advsum';s.appendChild(el)}
  const tx=id=>{const x=$('#'+id);if(!x)return '';if(x.tagName==='SELECT')return (x.options[x.selectedIndex]||{}).text||'';return x.value};
  const ps=[['優先度',tx('bp_pri')],['1日の上限',tx('bp_max')],['予備',tx('bp_ba')],['復習',tx('bp_cyc')]].filter(([,v])=>v&&v!=='0');
  el.textContent=ps.length?'いまの設定：'+ps.map(([k,v])=>k+' '+v).join('・'):''}
new MutationObserver(()=>{const d=$('#bp_adv');if(d&&!d.dataset.sum){d.dataset.sum='1';bpAdvSum();d.addEventListener('change',bpAdvSum);d.addEventListener('input',bpAdvSum)}}).observe(document.body,{childList:true,subtree:true});""")
rep('.acctdlg .box{max-width:440px}','.advsum{display:block;margin:2px 0 0 13px;font-size:11.5px;color:var(--fg)}\n.acctdlg .box{max-width:440px}')
# goal -> suggestions for tasks / books (#21-8)
rep("""${x.level!=='short'?`<button class="btn sm" data-gadd=""","""<button class="btn sm" data-gsug="${x.id}">提案</button>${x.level!=='short'?`<button class="btn sm" data-gadd=""")
rep("""/*@cloud*/""","""/*@cloud*/
function goalSugBooks(g){const ids=new Set(g.books||[]);goalDesc(g).forEach(c=>(c.books||[]).forEach(x=>ids.add(x)));return [...ids].map(book).filter(b=>b&&b.status!=='done')}
function openGoalSug(id){const g=goalById(id);if(!g)return;const today=todayKey(),lv=effLevel(g),bs=goalSugBooks(g),bids=new Set(bs.map(b=>b.id)),items=[];
  const add=(why,btn,act)=>items.push({why,btn,act});
  const planned=b=>b.sched||st.tasks.some(t=>t.source==='plan'&&t.planBook===b.id);
  bs.filter(b=>!planned(b)).forEach(b=>add(`「${esc(b.title)}」はまだ計画がありません。期限と1日の量から、毎日の予定を作れます。`,'逆算の計画を作る',`bplan:${b.id}`));
  if(!bs.length){const free=st.books.filter(b=>b.status==='active'&&!isSample(b)&&!st.goals.some(x=>!x.closed&&(x.books||[]).includes(b.id)));
    free.slice(0,4).forEach(b=>add(`教材「${esc(b.title)}」はどの目標にも結ばれていません。この目標のための教材にしますか？`,'この目標に結ぶ',`link:${b.id}`));
    add('この目標のための教材がまだありません。使う教材を登録すると、目標の日付から逆算した予定が作れます。','＋ 教材を追加','newbook')}
  if(g.due&&g.due>=today&&lv==='mid'&&!bs.some(b=>b.past))add('試験が目標なら、過去問・模試を回の単位で入れておくと、本番までに配分できます。','＋ 過去問・模試','past');
  if(lv==='mid'&&g.due&&g.due>addDays(today,3)&&!(g.ms||[]).some(m=>!m.done&&m.d>=today))add('本番までの中間の締め切り（段階）がありません。目標の編集画面の「試験のひな形を入れる」で、逆算した段階を作れます。','目標を編集','edit');
  (g.ms||[]).filter(m=>!m.done&&m.d>=today).sort((a,b)=>a.d<b.d?-1:1).slice(0,2).forEach(m=>{if(!st.tasks.some(t=>t.gms===m.id))add(`段階「${esc(m.t)}」（${mdw(m.d)}まで）を、今日のリストに出るタスクにできます。`,'タスクにする',`ms:${m.id}`)});
  const m=gMetric(g);if(m){const rs=(g.results||[]).slice().sort((a,b)=>a.d<b.d?-1:1),last=rs[rs.length-1];
    if((!last||daysBetween(last.d,today)>30)&&!st.tasks.some(t=>t.gmeasure===g.id&&!t.completed))add(last?`最後に結果を記録してから${daysBetween(last.d,today)}日たちました。模試や小テストで今の実力を測ると、計画を見直せます。`:'まだ結果の記録がありません。模試や小テストで今の実力を測っておくと、達成率がわかります。','測るタスクを作る','measure')}
  if(lv==='long'&&!st.goals.some(c=>c.parentId===g.id&&!c.closed))add('長期目標の下に、中期の目標（試験など）がありません。途中の目標を置くと、日々の予定につなげやすくなります。','＋ 中期目標','child:mid');
  if(lv==='mid'&&!st.goals.some(c=>c.parentId===g.id&&!c.closed))add('この目標の下に、短期の目標がありません（例：今月中に1周目を終える）。','＋ 短期目標','child:short');
  const wk=st.tasks.filter(t=>!t.completed&&t.due&&t.due>=today&&t.due<=addDays(today,6)&&(bids.has(t.book)||bids.has(t.planBook)||t.ggoal===g.id||(g.ms||[]).some(x=>x.id===t.gms))).length;
  openDrawer(`<div class="dh"><h3>この目標のための提案</h3><button class="btn" id="pclose">閉じる</button></div>
    <div class="bpsec"><b>${LVL[lv]}：${esc(g.title)}</b><small class="muted">${[g.due?fmtDay(g.due,true):'',bs.length?`教材 ${bs.length}冊`:'',`今後7日の予定 ${wk}件`].filter(Boolean).join('・')}</small></div>
    <div class="muted" style="font-size:12.5px;margin:2px 0 10px">目標の内容から、次にやるとよいことを並べました。押したものだけが追加されます。</div>
    ${items.length?items.map((x,i)=>`<div class="bpsec gsug"><span>${x.why}</span><button class="btn sm${i?'':' accent'}" data-gsa="${x.act}">${x.btn}</button></div>`).join(''):'<div class="bpsec">今のところ足りないものは見つかりませんでした。この調子で進めましょう。</div>'}`,()=>{
    $('#drawer').onclick=e=>{const b=e.target.closest('[data-gsa]');if(!b)return;const [k,v]=b.dataset.gsa.split(':'),back=()=>setTimeout(()=>openGoalSug(id),60);
      if(k==='bplan'){editBookPlan(v,back);return}
      if(k==='link'){g.books=g.books||[];if(!g.books.includes(v))g.books.push(v);const bk=book(v);if(bk)delete bk.noGoal;save();toast('目標に結びました','元に戻す',()=>{g.books=g.books.filter(x=>x!==v);save()});openGoalSug(id);return}
      if(k==='newbook'){const sid=(bs[0]||{}).subject;editBook(null,nb=>{g.books=g.books||[];if(!g.books.includes(nb))g.books.push(nb);save();setTimeout(()=>editBookPlan(nb,back),60)},sid?{subject:sid}:undefined);return}
      if(k==='past'){const sid=(bs[0]||{}).subject||'_';openPastWizard(sid,back);setTimeout(()=>{const s=$('#pw_g');if(s)s.value=g.id},40);return}
      if(k==='edit'){editGoal(id,null,back);return}
      if(k==='child'){editGoal(null,{level:v,parentId:id},back);return}
      if(k==='ms'){const ms=(g.ms||[]).find(x=>x.id===v);if(!ms)return;const b1=bs.length===1?bs[0]:null,t=newTask({title:ms.t,due:ms.d,gms:ms.id,ggoal:g.id,book:b1?b1.id:null,subject:b1?b1.subject:null,kind:b1?'study':'todo'});st.tasks.push(t);save();toast(`「${ms.t}」を${mdw(ms.d)}のタスクにしました`,'元に戻す',()=>{st.tasks=st.tasks.filter(x=>x!==t);save()});openGoalSug(id);return}
      if(k==='measure'){const d=addDays(today,7),t=newTask({title:`今の実力を測る（${g.title}）`,due:d,ggoal:g.id,gmeasure:g.id,notes:'結果は目標の「結果を記録」から入れます'});st.tasks.push(t);save();toast(`${mdw(d)}のタスクにしました`,'元に戻す',()=>{st.tasks=st.tasks.filter(x=>x!==t);save()});openGoalSug(id);return}}},'gsug')}
document.addEventListener('click',e=>{const x=e.target.closest('[data-gsug]');if(!x)return;e.stopPropagation();e.preventDefault();openGoalSug(x.dataset.gsug)},true);""")
rep('.acctdlg .box{max-width:440px}','.bpsec.gsug{display:flex;flex-direction:row;gap:10px;align-items:center;justify-content:space-between}.gsug span{font-size:13px;line-height:1.6}.gsug .btn{flex:none}\n.acctdlg .box{max-width:440px}')
# #25-2: Firestore rejects undefined values -> strip them; retry a few times on other errors
rep("this.write('m-'+mk,()=>({sessions:months[mk]||[]}))","this.write('m-'+mk,()=>({sessions:JSON.parse(JSON.stringify(months[mk]||[]))}))")
rep("try{await this.col.doc(id).set(fn())}catch(e){","this.retry=this.retry||{};try{await this.col.doc(id).set(fn());if(this.retry[id]){this.retry[id]=0;this.set('on','同期済み','同じアカウントで開いた端末どうしで同期されます')}}catch(e){")
rep("this.set('err','同期エラー',(e&&e.message)||'')}\n    this.busy[id]=false;","const n=this.retry[id]=(this.retry[id]||0)+1;if(n<=3){this.pend[id]=this.pend[id]||fn;this.set('err','同期エラー（再試行中）','この端末には保存されています。少し待って自動でもう一度送ります');setTimeout(()=>{this.busy[id]=false;this.flush(id)},4000*n);return}\n      this.retry[id]=0;this.set('err','同期エラー','この端末には保存されています。次に保存したときにもう一度送ります: '+((e&&e.message)||''))}\n    this.busy[id]=false;")
# #25-3: break-overrun bar: can be made small, can end the set, and moves out of the way of open dialogs
rep('<button class="ghost" id="ringCont" hidden>休憩せずに続けていた</button>','<button class="ghost" id="ringCont" hidden>休憩せずに続けていた</button><button class="ghost" id="ringEnd" hidden>セットを終える</button><button class="ghost" id="ringMin" hidden>小さくする</button>')
rep("function renderRing(){const bar=$('#ringbar');$('#ringCont').hidden=true;","function renderRing(){const bar=$('#ringbar');$('#ringCont').hidden=true;$('#ringEnd').hidden=$('#ringMin').hidden=true;if(!T.overrunSince)window.ringMini=false;bar.classList.toggle('mini',!!(T.overrunSince&&Ring.kind!=='clock'&&window.ringMini));")
rep("$('#ringCont').hidden=!liveBrkInfo()}","$('#ringCont').hidden=!liveBrkInfo();$('#ringEnd').hidden=$('#ringMin').hidden=false}")
rep("""/*@cloud*/""","""/*@cloud*/
document.addEventListener('click',e=>{const t=e.target,bar=$('#ringbar');if(!bar||!bar.contains(t))return;
  if(t.id==='ringMin'){e.stopPropagation();window.ringMini=true;renderRing();toast('右下の表示を押すと元に戻ります');return}
  if(t.id==='ringEnd'){e.stopPropagation();window.ringMini=false;endSet();return}
  if(bar.classList.contains('mini')){e.stopPropagation();window.ringMini=false;renderRing()}},true);""")
rep('.acctdlg .box{max-width:440px}','''.ringbar.mini{left:auto;right:12px;top:auto;bottom:calc(84px + env(safe-area-inset-bottom,0px));border-radius:999px;padding:8px 14px;gap:6px;animation:none;cursor:pointer;max-width:calc(100% - 24px)}
.ringbar.mini b{font-size:13px}.ringbar.mini span:has(>button){display:none!important}
body:has(.modal:not([hidden])) .ringbar:not(.mini),body:has(#detail:not([hidden])) .ringbar:not(.mini){top:auto;bottom:0;padding-top:10px;padding-bottom:calc(10px + env(safe-area-inset-bottom,0px));animation:none}
.acctdlg .box{max-width:440px}''')
# #25-1: bulk generation: a book set to start after another book in the same batch starts the day after that book's new plan ends
rep("${bs.map(b=>{const r=genBook(b,start);res[b.id]=r;const old=st.tasks","${orderByAfter(bs).map(b=>{const r=genChain(b,start,res);res[b.id]=r;const old=st.tasks")
rep("function afterChain(b){","function genChain(b,start,res){const a=b.sched&&b.sched.after,ra=a&&res[a];if(!ra||ra.err)return genBook(b,start);const keep=st.tasks;st.tasks=keep.filter(t=>!(t.source==='plan'&&t.planBook===a&&!t.completed)).concat(ra.tasks||[]);try{return genBook(b,start)}finally{st.tasks=keep}}\nfunction afterChain(b){")
# #25-4/5: the single-book preview used "today" while everything else starts from genStartDefault() (tomorrow after 18:00)
rep("const r=genBook(tmp,todayKey());$('#bp_prev').innerHTML=r.err?r.err:`今日から作ると: ${genText(tmp,r)}","const gs0=genStartDefault(),r=genBook(tmp,gs0),aw=tmp.sched&&tmp.sched.after&&book(tmp.sched.after),awn=aw&&!stageMode(tmp)&&!st.tasks.some(t=>t.source==='plan'&&t.planBook===aw.id&&!t.completed&&t.planKind!=='rv');$('#bp_prev').innerHTML=r.err?r.err:`${gs0===todayKey()?'今日':md(gs0)+'（18時以降は翌日）'}から作ると: ${genText(tmp,r)}${awn?`<br><small class=\"muted\">「${esc(aw.title)}」の予定がまだないので、すぐ始める計算です。「逆算して予定を作る」でまとめて作ると、「${esc(aw.title)}」が終わった翌日から始まります。</small>`:''}")
# #25-6: guide "使える時間" saves as soon as it changes (also when cleared)
rep("""/*@cloud*/""","""/*@cloud*/
document.addEventListener('change',e=>{const t=e.target;if(t.dataset&&t.dataset.gdm!=null){st.plan.dayMin[+t.dataset.gdm]=Math.round(Math.max(0,Math.min(16,+t.value||0))*60);save(true)}});""")
# #25-12: 0.25 h steps are valid
rep('step="0.5" data-dmin="${d}" value="${dm[d]?Math.round(dm[d]/30)/2:\'\'}"','step="0.25" data-dmin="${d}" value="${dm[d]?Math.round(dm[d]/15)/4:\'\'}"')
rep('step="0.5" data-gdm="${d}" value="${dm[d]?Math.round(dm[d]/30)/2:\'\'}"','step="0.25" data-gdm="${d}" value="${dm[d]?Math.round(dm[d]/15)/4:\'\'}"')
# #25-7: routines were counted twice in the 2-week check; planner count uses the same rule and says which period it covers
rep("+routinesOn(d).reduce((a,r)=>a+(+r.min||0),0)>c+1",">c+1",count=2)
rep("load[d]=loadOf(d,items[d]||[])+routinesOn(d).reduce((a,r)=>a+(+r.min||0),0)","load[d]=loadOf(d,items[d]||[])")
rep("if(c!=null&&loadOf(d,items[d]||[])>c+1)ov++}","if(c!=null&&c>0&&loadOf(d,items[d]||[])>c+1)ov++}")
rep("<b>使える時間を超える日が ${ov}日</b> あります","<b>使える時間を超える日が ${ov}日</b> あります（表示中の ${mdw(from<today?today:from)}〜${mdw(to)}・定番を含む）")
rep("使える時間を超える日 ${n}日（2週間以内）","使える時間を超える日 ${n}日（今日から2週間・定番を含む）")
# #25-9: routines without a time estimate are not in the day total -> say so
rep("${ld&&d>=today&&dayEst(es)?' 見積もり中':''}","${ld&&d>=today&&dayEst(es)?' 見積もり中':''}${es.some(e=>e.kind==='rt'&&!e.done&&!(+e.min))?'（時間の目安がない定番は含みません）':''}")
# #25-8: say what "plan tasks" counts
rep("${nPlan?`いま計画のタスクが ${nPlan}件 あります。","${nPlan?`いま逆算で作った計画のタスクが ${nPlan}件 あります（手動で足したタスクや定番は数えていません）。")
# #25-11: wording matches the button
rep("「確定」を押すとタスクとして登録されます。","「下書きに追加」で週間プランナーの下書きに入り、上の「確定」を押すとタスクとして登録されます。")
# #25-10: same-name books: warn once, and tell them apart in the "start after" list
rep("$('#e_save').onclick=()=>{const n=$('#e_title').value.trim();if(!n){toast('教材名を入力してください');$('#e_title').focus();return}","$('#e_save').onclick=()=>{const n=$('#e_title').value.trim();if(!n){toast('教材名を入力してください');$('#e_title').focus();return}if(st.books.some(x=>x!==b&&(x.title||'').trim()===n)&&$('#e_title').dataset.dupok!==n){$('#e_title').dataset.dupok=n;toast('同じ名前の教材がすでにあります。区別できる名前（例：「〜 2冊目」）にするか、このままでよければもう一度「保存」を押してください');$('#e_title').focus();return}")
rep("<option value=\"${x.id}\"${sc.after===x.id?' selected':''}>「${esc(x.title)}」が終わってから始める</option>","<option value=\"${x.id}\"${sc.after===x.id?' selected':''}>「${esc(x.title)}」${ch.some(y=>y!==x&&y.title===x.title)?`（${esc(((subj(x.subject)||{}).name)||'科目なし')}・${(x.id||'').slice(-4)}）`:''}が終わってから始める</option>")
# #25-12: why no new range lands on the last study day of the week; why auto == even
rep("'この教材では、3つとも同じ配り方になります'","(capOn0()?'この教材では、3つとも同じ配り方になります':'今は3つとも同じ配り方です。使える時間（計画の「3 使える時間・予定」）を曜日ごとに入れると、「自動」は時間の多い曜日に多く配ります')")
rep("$('#bp_prev').innerHTML=r.err?r.err:`${gs0===todayKey()?'今日':md(gs0)+'（18時以降は翌日）'}から作ると: ${genText(tmp,r)}","$('#bp_prev').innerHTML=r.err?r.err:`${gs0===todayKey()?'今日':md(gs0)+'（18時以降は翌日）'}から作ると: ${genText(tmp,r)}${!stageMode(tmp)&&bufOf(tmp).week>0?`<br><small class=\"muted\">毎週の予備日（週バッファー ${bufOf(tmp).week}%）として、週の最後の勉強日（月曜始まりなので、ふつうは日曜）には新しい範囲を入れません。遅れの取り戻しに使う日です。毎日入れたいときは、細かい設定の週バッファーを 0 にします。</small>`:''}")
# C-1: "＋ 予定" is a special-day mark, not a task -> name it so
rep('<button class="btn sm" data-addk="ev">＋ 予定</button>','<button class="btn sm" data-addk="ev">＋ 特別な日</button>')
rep('<button class="btn sm" id="shAddEv">＋ 予定</button>','<button class="btn sm" id="shAddEv">＋ 特別な日</button>')
rep('<button class="btn sm" id="gd_ev">＋ 予定（修学旅行・模試など）</button>','<button class="btn sm" id="gd_ev">＋ 特別な日（修学旅行・模試・休みなど）</button>')
rep('<h2 style="font-size:15px">日ごとの予定</h2><button class="btn sm" id="evAdd">＋ 予定</button>','<h2 style="font-size:15px">特別な日（行事・休み）</h2><button class="btn sm" id="evAdd">＋ 特別な日</button>')
rep("<h3>${isNew?'予定を追加':'予定を編集'}</h3>","<h3>${isNew?'特別な日を追加':'特別な日を編集'}</h3>")
rep('<input class="titlein" id="ev_title" value="${esc(ev.title)}" placeholder="例: 修学旅行、全統模試" maxlength="40">','<div class="muted" style="font-size:12.5px;margin:-4px 0 2px">修学旅行・模試・休みの日などの印です（タスクではありません）。その日の勉強の量を決めます。やることを足すときは「＋ タスク」「＋ 学習」から。</div>\n    <input class="titlein" id="ev_title" value="${esc(ev.title)}" placeholder="例: 修学旅行、全統模試" maxlength="40">')
# C-2: book detail shows its reviews and links to them
rep('<button class="btn" id="b_edit">${ICON.pen}編集</button></div>','<button class="btn" id="b_edit">${ICON.pen}編集</button></div>${(()=>{const rs=(st.reviews||[]).filter(r=>(r.book===b.id||r.fromBook===b.id)&&!r.done&&!r.paused);if(!rs.length&&!b.sched)return \'\';const nx=rs.map(r=>r.due).filter(Boolean).sort()[0],cy=(b.sched||{}).cycle;return `<div class="bpsec gsug"><span><b>復習</b>　${rs.length?`この教材の復習 ${rs.length}件${nx?`・次は ${mdw(nx)}`:\'\'}`:\'この教材の復習はまだありません\'}<small class="muted" style="display:block">${b.sched?(cy===\'no\'?\'計画のタスクを終えても復習には入れない設定です（教材の計画の「復習サイクル」で変えられます）\':`計画のタスクを終えると、その範囲を忘却曲線にそって復習に${cy===\'yes\'?\'入れます\':\'入れるか確認します\'}（教材の計画の「復習サイクル」で変えられます）`):\'\'}</small></span>${rs.length?`<button class="btn sm" data-bkrv="1">復習の一覧へ</button>`:\'\'}</div>`})()}')
rep("""/*@cloud*/""","""/*@cloud*/
document.addEventListener('click',e=>{if(!e.target.closest('[data-bkrv]'))return;closeDrawer();const tb=document.querySelector('#tabs [data-v="timer"]');if(tb)tb.click();setTimeout(()=>{tKind='review';LS.set('tkind',tKind);curList='upcoming';renderTasks();const tp=$('#taskPanel');if(tp)tp.scrollIntoView({behavior:'smooth',block:'start'})},80)});""")
# ---- feedback #28-#32 ----
# #31-1: unticking a book in the guide only leaves it out of this run; its plan settings stay
rep("else if(!ids.has(b.id)&&b.sched)delete b.sched;","else if(!ids.has(b.id)&&b.sched)gdSk().add(b.id);if(ids.has(b.id))gdSk().delete(b.id);")
rep("const on=!!b.sched,r=on?genBook(b,genStartDefault()):null","const on=!!b.sched&&!gdSk().has(b.id),r=on?genBook(b,genStartDefault()):null")
rep('<input type="checkbox" class="gd_b" value="${b.id}"${on?\' checked\':\'\'}><span>${esc(b.title)}','<input type="checkbox" class="gd_b" value="${b.id}"${on?\' checked\':\'\'}><span>${esc(b.title)}${b.sched&&!on?\'<small style="color:var(--muted)">（今回は作りません・計画の設定は残ります）</small>\':\'\'}')
rep("gdSubBooks(sid).filter(b=>b.sched)","gdSubBooks(sid).filter(b=>b.sched&&!gdSk().has(b.id))",count=2)
rep("b.sched&&subs.includes(sbKey(b))&&!isHand(b)","b.sched&&subs.includes(sbKey(b))&&!isHand(b)&&!gdSk().has(b.id)")
# #28-4: the shelf behind the book drawer shows the edit right away
rep("else openBook(b.id)};","else{openBook(b.id);renderView()}};")
# #30-3: a plan measured in time does not show a page cap
rep("${+sc.max?`・上限 ${uAmt(b,+sc.max)}/日`:''}","${+sc.max&&sc.nm!=='time'?`・上限 ${uAmt(b,+sc.max)}/日`:''}")
# #29-1: the set counter counts the same way while waiting and while running
rep("return `このセット: 集中 ${e.k+(T.mode==='focus'&&T.startedAt?1:0)}/${e.n} 回目・","return `このセット: ${T.mode==='focus'?`集中 ${Math.min(e.n,e.k+1)}/${e.n} 回目`:`集中 ${e.k}/${e.n} 回 済み`}・")
# #28-8: header timer follows a changed focus/break length at once
rep("if(['focus','short','long'].includes(k)&&!T.running&&!T.startedAt){T.total=T.remaining=durFor(T.mode);persistT()}","if(['focus','short','long'].includes(k)&&!T.running&&!T.startedAt){T.total=T.remaining=durFor(T.mode);persistT();renderTimer()}")
rep("""/*@cloud*/""","""/*@cloud*/
function gdSk(){return window.gdSkip=window.gdSkip||new Set()}
// #29-2: closing a study-task editor with unsaved changes asks first
document.addEventListener('input',e=>{if(e.target.closest&&e.target.closest('#drawer')&&$('#sp_save'))$('#drawer').dataset.dirty='1'},true);
document.addEventListener('change',e=>{if(e.target.closest&&e.target.closest('#drawer')&&$('#sp_save'))$('#drawer').dataset.dirty='1';if(e.target.id==='d_book')setTimeout(()=>toast('教材を変更しました（保存済み）'),50)},true);
document.addEventListener('click',e=>{const dr=$('#drawer');if(!dr||dr.dataset.dirty!=='1'||!$('#sp_save'))return;const isClose=e.target.id==='pclose'||e.target.id==='detail';if(!isClose)return;
  e.stopPropagation();e.preventDefault();const m=$('#modal');let alt=$('#modalAlt');if(!alt){alt=document.createElement('button');alt.id='modalAlt';alt.className='btn';$('#modalNo').after(alt)}alt.textContent='保存せずに閉じる';alt.hidden=false;
  const done=()=>{alt.hidden=true};alt.onclick=()=>{m.hidden=true;done();dr.dataset.dirty='';closeDrawer()};
  confirmBox('保存していない変更があります。保存しますか？','保存する',()=>{done();dr.dataset.dirty='';$('#sp_save').click();setTimeout(()=>{if(!$('#detail').hidden&&$('#sp_save')&&/保存しました/.test(($('#toastMsg')||{}).textContent||''))closeDrawer()},80)});const no=$('#modalNo').onclick;$('#modalNo').onclick=()=>{done();no&&no()}},true);
new MutationObserver(()=>{const dr=$('#drawer');if(dr)dr.dataset.dirty=''}).observe($('#drawer'),{childList:true});""")
# #30-1/#32-4: ticking off a planned range counts as progress (and re-planning starts after it)
rep("function bookProgress(b){if(!b)return 0;if(b.mode==='range')return b.pos||0;","function bookProgress(b){if(!b)return 0;if(b.mode==='range')return Math.max(b.pos||0,doneTo(b));")
# #30-2: a day does not show the same missed range twice
rep("((st.plan.miss||{})[d]||[]).forEach(m=>{if(seen.has(m.id))return;","((st.plan.miss||{})[d]||[]).forEach(m=>{if(seen.has(m.id)||out.some(o=>o.title===m.title))return;")
# #32-1: past papers placed in the buffer start early enough to finish by the deadline
rep("const n=addDays(s,1);return n>start?n:start}","let n=addDays(s,1);n=fitBuf(b,start,n);return n>start?n:start}")
# #30-4: "後ろへずらす" also moves reviews off the days with no study
rep("const n=x.dataset.of==='shift'?shiftOffTasks(list):offToBuf(list);","let n=x.dataset.of==='shift'?shiftOffTasks(list):offToBuf(list);if(x.dataset.of==='shift')n+=shiftOffReviews();")
rep("const n=k==='offshift'?shiftOffTasks(ov):offToBuf(ov);","let n=k==='offshift'?shiftOffTasks(ov):offToBuf(ov);if(k==='offshift')n+=shiftOffReviews();")
rep('<button data-of="shift">後ろへずらす<small>その教材の後ろの予定も順に1日ずつ送ります</small></button>','<button data-of="shift">後ろへずらす<small>その教材の後ろの予定も順に1日ずつ送ります。重なる復習も次の勉強日へ動かします</small></button>')
# #28-1 / #30-6: before re-planning, say what is replaced (and overdue ones), and warn about very long days
rep("$('#gn_go').onclick=()=>{const ids=$$('.gn_b').filter(c=>c.checked).map(c=>c.value);if(!ids.length){toast(Object.values(res).every(r=>r.err)?'どの教材も作れません。⚠ の「設定する」から直してください':'作る教材にチェックを入れてください');return}",
"$('#gn_go').onclick=()=>{const ids=$$('.gn_b').filter(c=>c.checked).map(c=>c.value);if(!ids.length){toast(Object.values(res).every(r=>r.err)?'どの教材も作れません。⚠ の「設定する」から直してください':'作る教材にチェックを入れてください');return}\n      if(!window.__gnOk){const today=todayKey(),oldAll=st.tasks.filter(t=>t.source==='plan'&&ids.includes(t.planBook)&&!t.completed),lateN=oldAll.filter(t=>t.due&&t.due<today).length,per={};ids.forEach(id=>((res[id]&&res[id].tasks)||[]).forEach(t=>{if(t.due)per[t.due]=(per[t.due]||0)+taskMin(t)}));const big=Object.entries(per).filter(([d,m])=>m>=360).sort((a,c)=>c[1]-a[1]);\n        if(oldAll.length||big.length){confirmBox(`${oldAll.length?`終わっていない計画のタスク ${oldAll.length}件${lateN?`（うち期限切れ ${lateN}件）`:''}を、新しい予定に置き換えます。${lateN?'期限切れの分は今日以降に配り直し、もとの日には「できなかった」の印が残ります。':''}`:''}${big.length?`1日 約${fmtHM(big[0][1])}になる日があります（${big.slice(0,3).map(([d])=>md(d)).join('・')}${big.length>3?' ほか':''}）。教材の「1日の上限」や曜日、使える時間を見直すと減らせます。`:''}このまま作りますか？`,'作る',()=>{window.__gnOk=1;try{$('#gn_go').click()}finally{window.__gnOk=0}});return}}")
rep("""/*@cloud*/""","""/*@cloud*/
const _dt={k:-1,m:new Map()};
function doneTo(b){const k=st.updatedAt||0;if(_dt.k!==k){_dt.k=k;_dt.m=new Map()}if(_dt.m.has(b.id))return _dt.m.get(b.id);
  const rs=st.tasks.filter(t=>t.completed&&(t.planBook===b.id||t.book===b.id)&&t.plan&&t.plan.type==='range'&&t.planKind!=='rv'&&!t.bufFill).map(t=>[+t.plan.from,+t.plan.to]).filter(r=>r[1]>0).sort((a,c)=>a[0]-c[0]);
  let cur=b.pos||0;for(const [f,z] of rs){if(f<=cur+1&&z>cur)cur=z}if(b.total)cur=Math.min(cur,+b.total);_dt.m.set(b.id,cur);return cur}
function fitBuf(b,start,n){const tg=bookTarget(b);if(!tg||!b.sched)return n;const left=bUnits(b).filter(u=>!unitDone(b,u.id)).length;if(!left)return n;const per=Math.max(1,+b.sched.max||1);let need=Math.ceil(left/per),d=tg,i=0;
  while(i<1500&&d>=start){if(bw(b,d)>0){need--;if(!need)break}d=addDays(d,-1);i++}return need?n:(d<n?d:n)}
function shiftOffReviews(){const today=todayKey();let n=0;(st.reviews||[]).forEach(r=>{if(r.paused||!r.due||r.due<today)return;let d=r.due,i=0;while(dayType(d)==='off'&&i<60){d=addDays(d,1);i++}if(d!==r.due){r.due=d;n++}});return n}""")
# #30-5 / #31-3: say whether "late" is against the deadline itself or the deadline minus reserve days
rep("${r.late?'（期限に間に合いません）':''}","${r.late?'（'+lateTxt(b,r)+'）':''}")
rep("${r.late?'・<span style=\"color:var(--pri1)\">期限に間に合いません</span>':''}","${r.late?'・<span style=\"color:var(--pri1)\">'+lateTxt(b,r)+'</span>':''}")
rep("${r2.late?'・<span style=\"color:var(--pri1)\">期限に間に合いません</span>':''}","${r2.late?'・<span style=\"color:var(--pri1)\">'+lateTxt(b,r2)+'</span>':''}")
rep("<br><span style=\"color:var(--pri1)\">期限 ${md(r.tgt)} に間に合いません${+tmp.sched.max?","<br><span style=\"color:var(--pri1)\">${lateTxt(tmp,r)}${+tmp.sched.max?")
rep("${r.late?`<br><span style=\"color:var(--pri1)\">期限 ${md(r.tgt)} に間に合いません</span>`:''}","${r.late?`<br><span style=\"color:var(--pri1)\">${lateTxt(b,r)}</span>`:''}")
# #31-4: what "1日あたり必要" in the outlook table means
rep("<h2>教材ごとの見通し</h2>","<h2>教材ごとの見通し</h2><p class=\"muted\" style=\"font-size:12px;margin:0 0 6px\">「1日あたり必要」は、残りの量を今日から期限までの学習日で割った数です。開始日が先の教材や、予備日をとっている教材は、計画の1日の量と違うことがあります。</p>")
# #28-5: an undo toast stays longer
rep("toastT=setTimeout(()=>$('#toast').hidden=true,act?6000:3500)}","toastT=setTimeout(()=>$('#toast').hidden=true,act?10000:3500)}")
# #31-5: a planner tile needs a clearer pull before it starts dragging
rep("else if(dist>6)pArm(e.clientX,e.clientY);return}","else if(dist>14)pArm(e.clientX,e.clientY);return}")
# #28-7: auto-resume after pause can be switched off
rep("<span>集中中の一時停止<small>1回の集中で一時停止できる合計時間。過ぎると自動で再開します</small></span>","<span>集中中の一時停止<small>1回の集中で一時停止できる合計時間。過ぎると自動で再開します（長く中断するときは「制限なし」に）</small></span>")
# #31-6: when the next review is counted from
rep('<p style="margin:0;font-size:13.5px" id="rvdQ">どのくらい覚えていましたか？</p>','<p style="margin:0;font-size:13.5px" id="rvdQ">どのくらい覚えていましたか？</p>\n  <small class="muted" style="font-size:11.5px">次の復習日は、実際に復習した日（今日）から数えます。忘却曲線は「最後に思い出した日」から進むためです。</small>')
# #28-6: "明日へ" next to "日付を変える" in task details
rep('<button class="btn" id="d_movejump" type="button">日付を変える</button>','<button class="btn" id="d_tomorrow" type="button">明日へ</button><button class="btn" id="d_movejump" type="button">日付を変える</button>')
# #32-5 / #28-3: what the day's achievement count includes
rep("d===today?[act?`実績 ${fmtHM(act)}`:'実績 0:00',tot?`達成 ${dn}/${tot}`:''","d===today?[act?`実績 ${fmtHM(act)}`:'実績 0:00',tot?`達成 ${dn}/${tot}（今日の分・遅れは含まない）`:''")
rep("""/*@cloud*/""","""/*@cloud*/
function lateTxt(b,r){const real=bookTarget(b);if(real&&r.tgt&&r.tgt<real)return `予備日を除いた ${md(r.tgt)} までに終わりません（期限 ${md(real)} には${r.end&&r.end<=real?'間に合います':'間に合いません'}）`;return `期限 ${md(r.tgt||real)} に間に合いません`}
// #31-2: a deadline in the past is pointed out before saving
document.addEventListener('change',e=>{if(e.target.id==='bp_target'&&e.target.value&&e.target.value<todayKey())toast('期限が過去の日付です。日付を確かめてください')});
document.addEventListener('click',e=>{if(e.target.id!=='bp_save'||window.__bpOk)return;const i=$('#bp_target');if(!i||!i.value||i.value>=todayKey())return;e.stopPropagation();e.preventDefault();
  confirmBox(`期限（${md(i.value)}）が過去の日付です。このまま保存しますか？`,'保存する',()=>{window.__bpOk=1;try{$('#bp_save').click()}finally{window.__bpOk=0}})},true);
// #28-6: move a task to tomorrow from its details
document.addEventListener('click',e=>{if(e.target.id!=='d_tomorrow')return;const t=taskById(detailId);if(!t)return;if(t.repeat&&t.repeat!=='none'){toast('繰り返しのタスクは「日付を変える」から動かしてください');return}
  const prev=t.due,nd=addDays(todayKey(),1);t.due=nd;closeDrawer();save();toast(`明日（${mdw(nd)}）へ移しました`,'元に戻す',()=>{t.due=prev;save()})});
// #28-2: overdue tasks can be moved to today in one go from the today list
{const _rt=renderTasks;renderTasks=function(){_rt.apply(this,arguments);try{if(curList!=='today'||query)return;const od=st.tasks.filter(t=>isOverdue(t)&&(!t.repeat||t.repeat==='none'));if(!od.length)return;
  $('#taskList').insertAdjacentHTML('afterbegin',`<li class="grp" style="display:flex;align-items:center;justify-content:space-between;gap:8px;color:var(--pri1)"><span>期限切れ ${od.length}件</span><span style="display:flex;gap:6px"><button class="btn sm" data-odmv="0">まとめて今日へ</button><button class="btn sm" data-odmv="1">まとめて明日へ</button></span></li>`)}catch(x){}}}
document.addEventListener('click',e=>{const b=e.target.closest('[data-odmv]');if(!b)return;const od=st.tasks.filter(t=>isOverdue(t)&&(!t.repeat||t.repeat==='none'));if(!od.length)return;const snap=od.map(t=>[t,t.due]),nd=addDays(todayKey(),+b.dataset.odmv);
  od.forEach(t=>{noteMiss(t,nd);t.due=nd});save();toast(`期限切れ ${od.length}件を${+b.dataset.odmv?'明日':'今日'}へ移しました`,'元に戻す',()=>{snap.forEach(([t,d])=>t.due=d);save()})});""")
# #37-7: no "past deadline" toast while the year is still being typed (e.g. 0002-11-30)
rep("if(e.target.id==='bp_target'&&e.target.value&&e.target.value<todayKey())toast(","if(e.target.id==='bp_target'&&e.target.value&&e.target.value<todayKey()&&+e.target.value.slice(0,4)>=new Date().getFullYear()-1)toast(")
# #37-1: say which task went back to "not done", with undo
rep("if(t.completed){t.completed=false;t.completedAt=null;save();return}","if(t.completed){const ca=t.completedAt;t.completed=false;t.completedAt=null;save();if(!o.noAsk)toast(`「${t.title.length>16?t.title.slice(0,16)+'…':t.title}」を未完了に戻しました`,'元に戻す',()=>{t.completed=true;t.completedAt=ca;save()});return}")
# ---- sync: edits made in an open screen are not lost when cloud data arrives (#34-#37) ----
# 1) merging keeps the local objects (an open editor holds references to them); when the cloud copy is newer, it is copied INTO the local object
rep("const mergeArr=(a,b)=>{a=a||[];b=b||[];const m=new Map(),order=[];","const mergeArr=(a,b)=>{a=a||[];b=b||[];const m=new Map(),order=[],la=new Set(a),lm=new Map(a.filter(x=>x&&x.id).map(x=>[x.id,x]));")
rep(".filter(it=>!(tomb[it.id]&&tomb[it.id]>=(it.u||0))).map(it=>JSON.parse(JSON.stringify(it)));",".filter(it=>!(tomb[it.id]&&tomb[it.id]>=(it.u||0))).map(it=>{if(la.has(it))return it;const c=JSON.parse(JSON.stringify(it)),o=lm.get(it.id);if(o){for(const k of Object.keys(o))delete o[k];return Object.assign(o,c)}return c});")
# 2) a cloud copy we have already merged is not merged again; 3) a big state is stored in several documents
rep("let rs=null;const rm={};","let rs=null;const rm={},sd={};")
rep("if(d.id==='state'){try{rs=v.json?JSON.parse(v.json):null}catch(e){}}","if(d.id==='state'||/^state-\\d+$/.test(d.id))sd[d.id]=v;")
rep("\n    let changed=false;\n    if(rs&&(rs.updatedAt||0)!==(st.updatedAt||0)&&!snap.metadata.hasPendingWrites){","\n    if(sd.state){const n=+sd.state.parts||1;let s=sd.state.json||'',ok=true;for(let i=1;i<n;i++){const c=sd['state-'+i];if(!c||c.updatedAt!==sd.state.updatedAt){ok=false;break}s+=c.json||''}if(ok&&s){try{rs=JSON.parse(s)}catch(e){}}}\n    let changed=false;\n    if(rs&&(rs.updatedAt||0)!==(st.updatedAt||0)&&(rs.updatedAt||0)!==this.rsAt&&!snap.metadata.hasPendingWrites){this.rsAt=rs.updatedAt||0;")
rep("pushStateNow(){if(!this.col)return;const j=JSON.stringify(st);this.write('state',()=>({json:j,updatedAt:st.updatedAt}))},","pushStateNow(){if(!this.col)return;const j=JSON.stringify(st),at=st.updatedAt,N=250000;if(j.length<=N){this.write('state',()=>({json:j,updatedAt:at}));return}\n    const ps=[];for(let i=0;i<j.length;){let e=Math.min(j.length,i+N);const c=j.charCodeAt(e-1);if(e<j.length&&c>=0xD800&&c<=0xDBFF)e--;ps.push(j.slice(i,e));i=e}\n    this.write('state',()=>({__docs:ps.map((p,i)=>i?['state-'+i,{json:p,updatedAt:at}]:['state',{json:p,parts:ps.length,updatedAt:at}])}))},")
rep("this.retry=this.retry||{};try{await this.col.doc(id).set(fn());if(this.retry[id]){this.retry[id]=0;this.set('on','同期済み','同じアカウントで開いた端末どうしで同期されます')}}catch(e){","this.retry=this.retry||{};this.errs=this.errs||{};try{const d=fn();if(d&&d.__docs){const fs=this.col.firestore;if(fs&&fs.batch){const bt=fs.batch();d.__docs.forEach(([k,v])=>bt.set(this.col.doc(k),v));await bt.commit()}else{for(const [k,v] of d.__docs.slice(1))await this.col.doc(k).set(v);await this.col.doc(d.__docs[0][0]).set(d.__docs[0][1])}}else await this.col.doc(id).set(d);delete this.errs[id];if(this.retry[id]){this.retry[id]=0;this.set('on','同期済み','同じアカウントで開いた端末どうしで同期されます')}}catch(e){")
# 4) a failed save keeps showing as an error (it is not hidden by the next "同期済み")
rep("this.retry[id]=0;this.set('err','同期エラー','この端末には保存されています。次に保存したときにもう一度送ります: '+((e&&e.message)||''))}","this.retry[id]=0;this.errs[id]=1;this.set('err','同期エラー','この端末には保存されています。次に保存したときにもう一度送ります: '+((e&&e.message)||''))}")
rep("if(!snap.metadata.fromCache)this.set('on','同期済み','同じアカウントで開いた端末どうしで同期されます')},","if(!snap.metadata.fromCache&&!Object.keys(this.errs||{}).length)this.set('on','同期済み','同じアカウントで開いた端末どうしで同期されます')},")
open(dst, 'w', encoding='utf-8').write(h)
print('ok', len(h))
