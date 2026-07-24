<template>
  <div class="bg-white rounded-xl shadow-sm border p-6">
    <div class="flex items-center gap-3 mb-4">
      <div class="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
        <svg class="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <div class="flex-1">
        <h3 class="font-semibold text-gray-800">{{ title }}</h3>
        <p v-if="subtitle" class="text-xs text-gray-500">{{ subtitle }}</p>
      </div>
      <button
        v-if="showReset"
        class="text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 px-3 py-1.5 rounded-lg transition-colors"
        @click="$emit('reset')"
      >
        Process another
      </button>
    </div>

    <slot />

    <div v-if="filename" class="mt-4 flex items-center gap-3 bg-gray-50 rounded-lg p-4">
      <div class="flex-shrink-0 w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center">
        <svg class="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <div class="flex-1 min-w-0">
        <div class="font-medium text-gray-800 truncate text-sm">{{ filename }}</div>
        <div v-if="fileSize" class="text-xs text-gray-500">{{ formatSize(fileSize) }}</div>
      </div>
      <button
        class="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
        @click="download"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        Download
      </button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  title: { type: String, default: "Done" },
  subtitle: { type: String, default: "" },
  filename: { type: String, default: "" },
  fileSize: { type: Number, default: 0 },
  blob: { type: Blob, default: null },
  showReset: { type: Boolean, default: false },
});

defineEmits(["reset"]);

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function download() {
  if (!props.blob) return;
  const url = URL.createObjectURL(props.blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = props.filename;
  a.click();
  URL.revokeObjectURL(url);
}
</script>
