import { redirect } from 'next/navigation';

import { auth } from '../(auth)/auth';

export default async function DocsRootPage() {
  const session = await auth();
  const kbId = session?.user?.selectedSpace?.knowledgeBaseId;

  if (!kbId) {
    redirect('/');
  }

  redirect(`/docs/${encodeURIComponent(kbId)}`);
}
