-- TADJ AI V1.4 production schema
create extension if not exists pgcrypto;
create extension if not exists vector with schema extensions;

create table if not exists public.profiles (
 id uuid primary key references auth.users(id) on delete cascade,
 display_name text, plan text not null default 'free', credits integer not null default 100,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists public.projects (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
 name text not null, created_at timestamptz not null default now()
);
create table if not exists public.jobs (
 id uuid primary key default gen_random_uuid(), user_id uuid references auth.users(id) on delete set null,
 project_id uuid references public.projects(id) on delete set null, kind text not null, status text not null default 'queued',
 model text, route text, prompt text, asset_url text, progress integer not null default 0,
 created_at timestamptz not null default now(), completed_at timestamptz
);
create table if not exists public.documents (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
 project_id uuid references public.projects(id) on delete cascade, name text not null, content_type text,
 created_at timestamptz not null default now()
);
create table if not exists public.document_chunks (
 id bigint generated always as identity primary key, document_id uuid not null references public.documents(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade, chunk_index integer not null, content text not null,
 embedding extensions.vector(384), created_at timestamptz not null default now()
);
create index if not exists document_chunks_user_idx on public.document_chunks(user_id);
create index if not exists document_chunks_embedding_hnsw on public.document_chunks using hnsw (embedding vector_cosine_ops);
create table if not exists public.usage_events (
 id bigint generated always as identity primary key, user_id uuid references auth.users(id) on delete cascade,
 kind text not null, credits integer not null, metadata jsonb default '{}'::jsonb, created_at timestamptz not null default now()
);
create table if not exists public.subscriptions (
 id text primary key, user_id uuid not null references auth.users(id) on delete cascade,
 status text not null, price_id text, current_period_end timestamptz, created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;
alter table public.projects enable row level security;
alter table public.jobs enable row level security;
alter table public.documents enable row level security;
alter table public.document_chunks enable row level security;
alter table public.usage_events enable row level security;
alter table public.subscriptions enable row level security;

drop policy if exists profiles_own on public.profiles;
create policy profiles_own on public.profiles for all using (auth.uid()=id) with check(auth.uid()=id);
drop policy if exists projects_own on public.projects;
create policy projects_own on public.projects for all using(auth.uid()=user_id) with check(auth.uid()=user_id);
drop policy if exists jobs_own on public.jobs;
create policy jobs_own on public.jobs for all using(auth.uid()=user_id) with check(auth.uid()=user_id);
drop policy if exists documents_own on public.documents;
create policy documents_own on public.documents for all using(auth.uid()=user_id) with check(auth.uid()=user_id);
drop policy if exists chunks_own on public.document_chunks;
create policy chunks_own on public.document_chunks for all using(auth.uid()=user_id) with check(auth.uid()=user_id);
drop policy if exists usage_own on public.usage_events;
create policy usage_own on public.usage_events for select using(auth.uid()=user_id);
drop policy if exists subscriptions_own on public.subscriptions;
create policy subscriptions_own on public.subscriptions for select using(auth.uid()=user_id);

create or replace function public.handle_new_user() returns trigger language plpgsql security definer set search_path=public as $$
begin insert into public.profiles(id,display_name) values(new.id,coalesce(new.raw_user_meta_data->>'full_name',new.email)) on conflict(id) do nothing; return new; end; $$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users for each row execute procedure public.handle_new_user();

create or replace function public.match_document_chunks(query_embedding extensions.vector(384), match_count int default 6, filter_user_id uuid default auth.uid())
returns table(id bigint,document_id uuid,content text,similarity float) language sql stable as $$
 select c.id,c.document_id,c.content,1-(c.embedding <=> query_embedding) as similarity
 from public.document_chunks c where c.user_id=filter_user_id and c.embedding is not null
 order by c.embedding <=> query_embedding limit match_count;
$$;

create or replace function public.consume_credits(p_user_id uuid,p_cost integer,p_kind text,p_metadata jsonb default '{}'::jsonb)
returns boolean language plpgsql security definer set search_path=public as $$
declare ok boolean;
begin update profiles set credits=credits-p_cost,updated_at=now() where id=p_user_id and credits>=p_cost returning true into ok;
 if ok then insert into usage_events(user_id,kind,credits,metadata) values(p_user_id,p_kind,p_cost,p_metadata); return true; end if; return false;
end; $$;

-- Conversations / persistent chat history
create table if not exists public.conversations (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
 project_id uuid references public.projects(id) on delete set null, title text not null default 'New chat',
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists public.messages (
 id bigint generated always as identity primary key, conversation_id uuid not null references public.conversations(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade, role text not null check(role in ('user','assistant','system')),
 content text not null, sources jsonb not null default '[]'::jsonb, created_at timestamptz not null default now()
);
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
drop policy if exists conversations_own on public.conversations;
create policy conversations_own on public.conversations for all using(auth.uid()=user_id) with check(auth.uid()=user_id);
drop policy if exists messages_own on public.messages;
create policy messages_own on public.messages for all using(auth.uid()=user_id) with check(auth.uid()=user_id);
create index if not exists conversations_user_updated_idx on public.conversations(user_id,updated_at desc);
create index if not exists messages_conversation_idx on public.messages(conversation_id,created_at);

-- Private asset bucket. The API uses the service role; browser access remains RLS-protected.
insert into storage.buckets (id,name,public,file_size_limit)
values ('tadj-assets','tadj-assets',false,52428800)
on conflict (id) do nothing;
