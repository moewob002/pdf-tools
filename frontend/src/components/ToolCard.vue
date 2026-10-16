<template>
  <router-link :to="tool.path" class="card-interactive group flex items-start gap-4 p-5">
    <span class="tool-chip" :class="`tool-${tool.category}`">
      <ToolIcon :path="tool.icon" class="h-6 w-6" />
    </span>
    <span class="min-w-0 flex-1">
      <span class="block font-semibold text-fg">{{ tool.title }}</span>
      <span class="mt-1 block text-sm text-muted">{{ tool.desc }}</span>
      <span v-if="tool.tags?.length" class="mt-3 flex flex-wrap gap-1.5">
        <span v-for="tag in tool.tags" :key="tag" class="chip bg-surface-2 text-muted">{{ tag }}</span>
      </span>
    </span>
    <svg class="mt-1 h-5 w-5 shrink-0 text-muted transition-transform group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
    </svg>
  </router-link>
</template>

<script setup>
import ToolIcon from "./ToolIcon.vue";

defineProps({ tool: { type: Object, required: true } });
</script>
