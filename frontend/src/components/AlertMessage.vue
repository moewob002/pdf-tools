<template>
  <div
    :role="tone === 'error' ? 'alert' : 'status'"
    class="flex items-start gap-3 rounded-xl border px-4 py-3 text-sm"
    :class="styles.box"
  >
    <svg class="mt-0.5 h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="styles.icon" />
    </svg>
    <div class="min-w-0">
      <p class="font-semibold">{{ title || styles.title }}</p>
      <div class="mt-0.5 break-words text-fg"><slot /></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  tone: { type: String, default: "error" }, // error | warning | info | success
  title: { type: String, default: "" },
});

const TONES = {
  error: { box: "border-danger/30 bg-danger/10 text-danger", title: "Something went wrong", icon: "M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" },
  warning: { box: "border-warning/30 bg-warning/10 text-warning", title: "Heads up", icon: "M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" },
  info: { box: "border-info/30 bg-info/10 text-info", title: "Note", icon: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" },
  success: { box: "border-success/30 bg-success/10 text-success", title: "Done", icon: "M9 12l2 2 4-4m6 2a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" },
};

const styles = computed(() => TONES[props.tone] || TONES.error);
</script>
