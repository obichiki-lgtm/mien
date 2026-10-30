// Firestore の feedback/{id}（processed == false）を GitHub Issue にして processed = true にする。
// GitHub Actions（.github/workflows/feedback.yml）から実行。FIREBASE_SA はサービスアカウント鍵の JSON。
import { initializeApp, cert } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';

const { FIREBASE_SA, GITHUB_TOKEN, REPO } = process.env;
if (!FIREBASE_SA) {
  console.log('FIREBASE_SA が未設定のためスキップします');
  process.exit(0);
}
initializeApp({ credential: cert(JSON.parse(FIREBASE_SA)) });
const db = getFirestore();

async function gh(path, body) {
  const r = await fetch(`https://api.github.com/repos/${REPO}${path}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${GITHUB_TOKEN}`, Accept: 'application/vnd.github+json', 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (r.status === 422 && path === '/labels') return null; // ラベルは作成済み
  if (!r.ok) throw new Error(`${path} ${r.status} ${await r.text()}`);
  return r.json();
}

const KIND = { idea: '要望', bug: '不具合', other: 'その他' };
// 利用者の文章でメンションや Issue 参照が飛ばないようにする
const defuse = (t) => t.replace(/@/g, '@​').replace(/#(\d)/g, '#​$1');

await gh('/labels', { name: 'feedback', color: 'D9452B', description: 'アプリから届いたご意見・要望' });
const snap = await db.collection('feedback').where('processed', '==', false).limit(50).get();
for (const doc of snap.docs) {
  const v = doc.data();
  const text = defuse(String(v.text || '').slice(0, 2000));
  const kind = KIND[v.kind] || 'その他';
  const at = v.at && v.at.toDate ? v.at.toDate().toISOString() : '';
  const issue = await gh('/issues', {
    title: `[${kind}] ${text.replace(/\s+/g, ' ').slice(0, 50)}`,
    labels: ['feedback'],
    body: [
      text.split('\n').map((l) => '> ' + l).join('\n'),
      '',
      `- 種類: ${kind}`,
      `- 受信: ${at}`,
      `- 画面: ${String(v.page || '').slice(0, 20)}`,
      `- ログイン: ${v.uid ? 'あり' : 'なし'}`,
      `- 端末: ${defuse(String(v.ua || '').slice(0, 300))}`,
      '',
      `<!-- feedback-id: ${doc.id} -->`,
    ].join('\n'),
  });
  await doc.ref.update({ processed: true, issue: issue.number });
  console.log(`feedback ${doc.id} -> #${issue.number}`);
}
console.log(`${snap.size} 件を処理しました`);
