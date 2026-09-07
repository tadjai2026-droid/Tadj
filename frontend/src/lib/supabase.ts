
import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined;

export const supabase = url && key ? createClient(url, key) : null;

export async function signInGoogle() {
  if (!supabase) throw new Error('Supabase غير مهيأ. أضف VITE_SUPABASE_URL و VITE_SUPABASE_PUBLISHABLE_KEY.');
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: window.location.origin }
  });
  if (error) throw error;
}

export async function signOut() {
  if (supabase) await supabase.auth.signOut();
}
