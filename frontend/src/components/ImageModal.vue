<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
        @click.self="close"
      >
        <div
          ref="dialog"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
          class="card flex max-h-[90vh] w-full max-w-4xl flex-col"
          @keydown.esc="close"
          @keydown.tab="trapFocus"
        >
          <div class="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
            <h2 :id="titleId" class="truncate text-sm font-semibold text-fg">{{ title }}</h2>
            <button ref="closeButton" type="button" class="btn-icon" aria-label="Close preview" @click="close">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="flex flex-1 items-center justify-center overflow-auto rounded-b-2xl bg-surface-2 p-4">
            <img v-if="src" :src="src" :alt="title" class="max-h-[78vh] max-w-full rounded bg-white object-contain shadow" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { nextTick, ref, useId, watch } from "vue";

const props = defineProps({
  show: { type: Boolean, default: false },
  src: { type: String, default: "" },
  title: { type: String, default: "Page Preview" },
});

const emit = defineEmits(["close"]);

const titleId = useId();
const dialog = ref(null);
const closeButton = ref(null);
let returnFocusTo = null;

watch(
  () => props.show,
  async (open) => {
    if (open) {
      returnFocusTo = document.activeElement;
      await nextTick();
      closeButton.value?.focus();
    } else if (returnFocusTo instanceof HTMLElement) {
      returnFocusTo.focus();
      returnFocusTo = null;
    }
  }
);

function close() {
  emit("close");
}

// The only focusable control is the close button, so keep focus there.
function trapFocus(e) {
  e.preventDefault();
  closeButton.value?.focus();
}
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
