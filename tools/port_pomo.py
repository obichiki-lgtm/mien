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
      if(!u){this.set('','この端末に保存','設定 > データ から Google でログインすると端末間で同期されます');
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
"""async function cloudLogin(){try{await PomoCloud.signIn();location.reload()}catch(e){if(e&&e.code!=='auth/popup-closed-by-user'&&e.code!=='auth/cancelled-popup-request')toast('ログインできませんでした（'+(e.code||e.message||'')+'）')}}
async function saveFile(name,data){""")

open(dst, 'w', encoding='utf-8').write(h)
print('ok', len(h))
