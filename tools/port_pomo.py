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
    signIn(){return auth.signInWithPopup(new firebase.auth.GoogleAuthProvider())},
    signOut(){return auth.signOut()}};
})();
</script>
'''
rep('<!doctype html><html><head>', '<!doctype html><html lang="ja"><head>')
rep('<title>Pomo Timer</title>', '<title>Pomo Timer</title>\n' + FB)

# 2. Sync.init: claude.ai runtime when present, Firebase otherwise
rep("""    if(!window.claude||!window.claude.use){this.set('','この端末に保存','同期は claude.ai で開いたときに使えます');return}""",
"""    if(!window.claude||!window.claude.use){
      const pc=window.PomoCloud;if(!pc){this.set('','この端末に保存');return}
      const u=await pc.ready;
      if(!u){this.set('login','この端末に保存 · ログイン','クリックすると Google でログインし、端末間で同期します');
        if(!LS.get('loginHint',false)){LS.set('loginHint',true);setTimeout(()=>toast('Google でログインすると、ほかの端末と記録を同期できます','ログイン',cloudLogin),2500)}return}
      this.col=pc.col(u.uid);this.set('','同期中…');
      this.col.onSnapshot(snap=>this.onSnap(snap),err=>this.set('err','同期エラー','この端末には保存されています: '+(err&&err.code||'')));
      return}""")

# 3. settings row: account status + login / logout
rep("""<div class="pr"><span>同期<small>${Sync.col?'同じアカウントで開いた端末どうしで自動同期しています':'この端末のブラウザに保存中。claude.ai にサインインして開くと同期されます'}</small></span></div>""",
"""<div class="pr"><span>同期<small>${Sync.col?(window.PomoCloud&&PomoCloud.user?esc(PomoCloud.user.email||'')+' でログイン中。同じアカウントの端末どうしで自動同期しています':'同じアカウントで開いた端末どうしで自動同期しています'):(window.PomoCloud?'この端末のブラウザに保存中。Google でログインすると端末間で同期されます':'この端末のブラウザに保存中。claude.ai にサインインして開くと同期されます')}</small></span>${window.PomoCloud?(PomoCloud.user?'<button class="btn" id="d_logout">ログアウト</button>':'<button class="btn accent" id="d_login">Google でログイン</button>'):''}</div>""")

# 4. handlers
rep("""  if(t.id==='d_export')exportData();if(t.id==='d_import')$('#importFile').click();""",
"""  if(t.id==='d_export')exportData();if(t.id==='d_import')$('#importFile').click();
  if(t.id==='d_login'){cloudLogin();return}
  if(t.id==='d_logout'){confirmBox('ログアウトしますか？この端末に保存されたデータも消去されます（クラウドのデータは残ります）。','ログアウト',async()=>{await PomoCloud.signOut();for(const k of Object.keys(localStorage))if(k.startsWith('pf2_'))localStorage.removeItem(k);location.reload()});return}""")

rep("""async function saveFile(name,data){""",
"""if(window.PomoCloud&&new URLSearchParams(location.search).get('import')==='sched'){history.replaceState(null,'',location.pathname);PomoCloud.ready.then(()=>setTimeout(importSched,1200))}
async function cloudLogin(){try{await PomoCloud.signIn();location.reload()}catch(e){if(e&&e.code!=='auth/popup-closed-by-user'&&e.code!=='auth/cancelled-popup-request')toast('ログインできませんでした（'+(e.code||e.message||'')+'）')}}
async function saveFile(name,data){""")

# top-bar sync indicator: logged out -> sign in, signed in -> open settings
rep("""Sync.init();""","""if(window.PomoCloud&&!(window.claude&&window.claude.use)){const sy=$('#sync');sy.classList.add('tap');sy.setAttribute('role','button');sy.tabIndex=0;
  const act=()=>{if(!Sync.col)cloudLogin();else go('prefs')};sy.addEventListener('click',act);sy.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();act()}})}
Sync.init();""")
rep('.sync.on b{background:var(--tree)} .sync.err b{background:var(--pri1)}',
    '.sync.on b{background:var(--tree)} .sync.err b{background:var(--pri1)}\n.sync.tap{cursor:pointer;padding:4px 10px;border-radius:999px}.sync.tap:hover{background:var(--surface);color:var(--fg);box-shadow:0 0 0 1px var(--line)}.sync.login b{background:var(--focus)}')

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
rep("""async function cloudLogin(){""","""/* 学習スケジューラー → Pomo Timer. Source: Firestore users/{uid} when signed in, else this origin's localStorage.
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
    st.reviews.push(...p.rv);st.tasks.push(...p.tk);st.memos.push(...p.mm);save();renderPrefs();toast(`取り込みました（復習 ${p.rv.length}・タスク ${p.tk.length}・メモ ${p.mm.length}）`)})}
async function cloudLogin(){""")

open(dst, 'w', encoding='utf-8').write(h)
print('ok', len(h))
