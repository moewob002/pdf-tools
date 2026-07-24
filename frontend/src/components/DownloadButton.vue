<template>
  <button
    class="inline-flex items-center px-5 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
    :class="[
      loading ? 'bg-indigo-500 cursor-wait' : '',
    ]"
    :disabled="disabled || loading"
    @click="$emit('click')"
  >
    <template v-if="loading">
      <svg
        class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      <span>Processing...</span>
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
});

defineEmits(["click"]);
</script>
