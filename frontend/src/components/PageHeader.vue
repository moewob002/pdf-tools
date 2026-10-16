<template>
  <header class="mb-8 flex items-start gap-3 sm:gap-4">
    <router-link v-if="back" :to="back.path" class="btn-icon mt-1 shrink-0" :aria-label="`Back to ${back.label}`">
      <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </router-link>
    <span class="tool-chip" :class="`tool-${category}`">
      <ToolIcon :path="icon" class="h-6 w-6" />
    </span>
    <div class="min-w-0">
      <h1 class="text-2xl font-bold tracking-tight text-fg sm:text-3xl">{{ title }}</h1>
      <p v-if="description" class="mt-1 text-sm text-muted sm:text-base">{{ description }}</p>
    </div>
  </header>
</template>

<script setup>
import ToolIcon from "./ToolIcon.vue";

defineProps({
  title: { type: String, required: true },
  description: { type: String, default: "" },
  category: { type: String, required: true },
  icon: { type: String, required: true },
  back: { type: Object, default: null }, // { path, label }
});
</script>
