<template>
  <section class="card p-5 sm:p-6" :aria-labelledby="headingId">
    <div class="mb-4 flex items-center gap-3">
      <span class="step-badge" aria-hidden="true">{{ number }}</span>
      <div class="min-w-0">
        <h2 :id="headingId" class="font-semibold text-fg">
          <span class="sr-only">Step {{ number }}: </span>{{ title }}
        </h2>
        <p v-if="hint" class="text-sm text-muted">{{ hint }}</p>
      </div>
    </div>
    <slot />
  </section>
</template>

<script setup>
import { useId } from "vue";

defineProps({
  number: { type: Number, required: true },
  title: { type: String, required: true },
  hint: { type: String, default: "" },
});

const headingId = useId();
</script>
