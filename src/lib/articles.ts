import { getCollection } from 'astro:content';

export async function getPublished() {
  const now = new Date();
  const all = await getCollection('articles', ({ data }) => !data.draft && data.publishDate <= now);
  return all.sort((a, b) => b.data.publishDate.valueOf() - a.data.publishDate.valueOf());
}

export const fmt = (d: Date) =>
  d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC' });
