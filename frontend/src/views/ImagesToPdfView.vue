<template>
  <div class="max-w-4xl mx-auto">
    <div class="flex items-center gap-3 mb-6">
      <router-link
        to="/"
        class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </router-link>
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Images to PDF</h2>
        <p class="text-sm text-gray-500">Combine multiple images into a single PDF</p>
      </div>
    </div>

    <div class="space-y-6">
      <div v-if="!resultBlob" class="bg-white rounded-xl shadow-sm border p-6">
        <FileUpload
          ref="fileUpload"
          accept="image/*"
          accept-text="PNG, JPG, TIFF, BMP images"
          :multiple="true"
          @update:files="(f) => (files = f)"
        />
        <div v-if="files.length > 0" class="mt-4">
          <p class="text-xs text-gray-500">{{ files.length }} image{{ files.length !== 1 ? 's' : '' }} will be combined</p>
        </div>
        <div class="mt-4">
          <DownloadButton
            :loading="loading"
            :disabled="files.length === 0"
            @click="convert"
          >
            Convert to PDF
          </DownloadButton>
        </div>
      </div>

      <ResultCard
        v-if="resultBlob"
        title="Images Converted to PDF"
        :subtitle="`${imageCount} images combined into one PDF`"
        filename="converted.pdf"
        :file-size="resultBlob.size"
        :blob="resultBlob"
        :show-reset="true"
        @reset="reset"
      />

      <div v-if="error" class="bg-red-50 text-red-700 rounded-lg p-4 text-sm">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import api from "../api";
import { getErrorMessage } from "../utils/errors";
import FileUpload from "../components/FileUpload.vue";
import DownloadButton from "../components/DownloadButton.vue";
import ResultCard from "../components/ResultCard.vue";

const files = ref([]);
const loading = ref(false);
const error = ref("");
const fileUpload = ref(null);
const resultBlob = ref(null);
const imageCount = ref(0);

async function convert() {
  loading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    files.value.forEach((f) => form.append("files", f));
    const res = await api.post("/convert/image-to-pdf", form, { responseType: "blob" });
    resultBlob.value = res.data;
    imageCount.value = files.value.length;
  } catch (e) {
    error.value = await getErrorMessage(e, "Conversion failed");
  } finally {
    loading.value = false;
  }
}

function reset() {
  resultBlob.value = null;
  imageCount.value = 0;
  files.value = [];
  error.value = "";
  if (fileUpload.value) fileUpload.value.clear();
}
</script>
