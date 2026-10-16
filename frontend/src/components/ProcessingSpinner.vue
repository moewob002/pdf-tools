<template>
  <div role="status" aria-live="polite" class="flex flex-col items-center justify-center py-10 text-center">
    <div class="relative h-14 w-14" aria-hidden="true">
      <div class="absolute inset-0 rounded-full border-4 border-primary/15"></div>
      <div class="absolute inset-0 animate-spin rounded-full border-4 border-transparent border-r-secondary border-t-primary"></div>
    </div>
    <p class="mt-5 font-semibold text-fg">{{ message }}</p>
    <p v-if="submessage" class="mt-1 text-sm text-muted">{{ submessage }}</p>
  </div>
</template>

<script setup>
defineProps({
  message: { type: String, default: "Processing…" },
  submessage: { type: String, default: "" },
});
</script>
