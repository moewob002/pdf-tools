<template>
  <span class="chip shrink-0" :class="look.cls">
    <svg
      class="h-3.5 w-3.5"
      :class="status.state === 'loading' ? 'animate-spin' : ''"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      aria-hidden="true"
    >
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" :d="look.icon" />
    </svg>
    {{ status.label }}
  </span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  status: { type: Object, required: true }, // { state: "ready" | "loading" | "error", label }
});

const LOOKS = {
  ready: { cls: "bg-success/10 text-success", icon: "M5 13l4 4L19 7" },
  loading: { cls: "bg-info/10 text-info", icon: "M12 3a9 9 0 1 0 9 9" },
  error: { cls: "bg-danger/10 text-danger", icon: "M6 18 18 6M6 6l12 12" },
};

const look = computed(() => LOOKS[props.status.state] || LOOKS.ready);
</script>
