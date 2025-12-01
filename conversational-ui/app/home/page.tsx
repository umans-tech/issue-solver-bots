import { redirect } from 'next/navigation';

// Keep /home as an alias of /landing
export default function HomeAlias() {
  redirect('/landing');
}
