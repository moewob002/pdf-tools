<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="$emit('close')"
      >
        <div class="bg-white rounded-xl shadow-2xl max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col">
          <div class="flex items-center justify-between px-4 py-3 border-b">
            <h3 class="text-sm font-medium text-gray-700">{{ title }}</h3>
            <button
              class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
              @click="$emit('close')"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="flex-1 overflow-auto p-4 flex items-center justify-center bg-gray-50 rounded-b-xl">
            <img
              v-if="src"
              :src="src"
              :alt="title"
              class="max-w-full max-h-[80vh] object-contain rounded shadow"
            />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  show: { type: Boolean, default: false },
  src: { type: String, default: "" },
  title: { type: String, default: "Page Preview" },
});

defineEmits(["close"]);
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
