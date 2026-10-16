<template>
  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="path" />
  </svg>
</template>

<script setup>
defineProps({ path: { type: String, required: true } });
</script>
