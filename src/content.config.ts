import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

export const CATEGORIES = {
  'how-the-body-works': 'How the Body Works',
  'sleep': 'Sleep',
  'nutrition-basics': 'Nutrition Basics',
  'movement': 'Movement & Fitness',
  'mind': 'Mind & Brain',
  'everyday-health': 'Everyday Health Questions',
} as const;

const articles = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/articles' }),
  schema: z.object({
    title: z.string().max(80),
    description: z.string().min(80).max(170),
    category: z.enum(Object.keys(CATEGORIES) as [keyof typeof CATEGORIES, ...(keyof typeof CATEGORIES)[]]),
    keywords: z.array(z.string()).min(1),
    publishDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    readingMinutes: z.number().int().positive(),
    faq: z.array(z.object({ q: z.string(), a: z.string() })).default([]),
    sources: z.array(z.object({ title: z.string(), url: z.string().url() })).min(3),
    draft: z.boolean().default(false),
  }),
});

export const collections = { articles };
