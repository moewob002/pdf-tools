<template>
  <button
    type="button"
    :class="variant === 'secondary' ? 'btn-secondary' : 'btn-primary'"
    class="min-w-[9rem] px-5 py-3 text-base"
    :disabled="disabled || loading"
    :aria-busy="loading ? 'true' : 'false'"
    @click="$emit('click')"
  >
    <template v-if="loading">
      <svg class="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24" aria-hidden="true">
        <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.4 0 0 5.4 0 12h4z" />
      </svg>
      <span>{{ loadingText }}</span>
    </template>
    <template v-else>
      <slot />
    </template>
  </button>
</template>

<script setup>
defineProps({
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  loadingText: { type: String, default: "Processing…" },
  variant: { type: String, default: "primary" },
});

defineEmits(["click"]);
</script>
