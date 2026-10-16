<template>
  <div class="mx-auto max-w-5xl">
    <section class="relative isolate mb-12 overflow-hidden rounded-3xl border border-line bg-surface px-6 py-12 text-center sm:px-12 sm:py-16">
      <div class="pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
        <div class="hero-blob left-[-10%] top-[-30%] bg-primary"></div>
        <div class="hero-blob right-[-12%] top-[-20%] bg-secondary"></div>
        <div class="hero-blob bottom-[-45%] left-[20%] bg-cyan"></div>
        <div class="hero-blob bottom-[-40%] right-[5%] bg-accent"></div>
      </div>
      <p class="chip mx-auto mb-4 bg-surface text-muted ring-1 ring-line">
        <svg class="h-3.5 w-3.5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 15v2m-6 4h12a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2zm10-10V7a4 4 0 0 0-8 0v4h8z" />
        </svg>
        Self-hosted · no third-party services
      </p>
      <h1 class="text-4xl font-extrabold tracking-tight text-fg sm:text-5xl">
        Every PDF job, <span class="text-gradient">one place</span>.
      </h1>
      <p class="mx-auto mt-4 max-w-xl text-base text-muted sm:text-lg">
        Convert, edit, OCR and compress PDFs. Pick a tool, drop your file, download the result.
      </p>
      <ol class="mx-auto mt-8 flex max-w-lg flex-col justify-center gap-3 text-left text-sm sm:flex-row sm:gap-6">
        <li v-for="(step, i) in steps" :key="step" class="flex items-center gap-2 text-fg">
          <span class="step-badge h-6 w-6 text-xs" aria-hidden="true">{{ i + 1 }}</span>
          {{ step }}
        </li>
      </ol>
    </section>

    <section v-for="(category, key) in CATEGORIES" :key="key" class="mb-10" :aria-labelledby="`cat-${key}`">
      <div class="mb-4 flex items-center gap-3">
        <span class="tool-chip h-9 w-9" :class="`tool-${key}`">
          <ToolIcon :path="category.icon" class="h-5 w-5" />
        </span>
        <div>
          <h2 :id="`cat-${key}`" class="text-lg font-bold text-fg">{{ category.title }}</h2>
          <p class="text-sm text-muted">{{ category.desc }}</p>
        </div>
      </div>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <ToolCard v-for="tool in toolsIn(key)" :key="tool.id" :tool="tool" />
      </div>
    </section>
  </div>
</template>

<script setup>
import ToolCard from "../components/ToolCard.vue";
import ToolIcon from "../components/ToolIcon.vue";
import { CATEGORIES, toolsIn } from "../tools";

const steps = ["Pick a tool", "Upload your file", "Download the result"];
</script>

<style scoped>
.hero-blob {
  position: absolute;
  height: 22rem;
  width: 22rem;
  border-radius: 9999px;
  filter: blur(60px);
  opacity: var(--hero-blob-opacity);
}
</style>
