<template>
  <div class="flex flex-col items-center justify-center py-12">
    <div class="relative">
      <div class="w-16 h-16 rounded-full border-4 border-indigo-200"></div>
      <div class="absolute top-0 left-0 w-16 h-16 rounded-full border-4 border-transparent border-t-indigo-600 animate-spin"></div>
    </div>
    <p class="mt-6 text-gray-700 font-medium">{{ message }}</p>
    <p v-if="submessage" class="mt-1 text-sm text-gray-500">{{ submessage }}</p>
  </div>
</template>

<script setup>
defineProps({
  message: { type: String, default: "Processing..." },
  submessage: { type: String, default: "" },
});
</script>
