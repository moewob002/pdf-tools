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
        <h2 class="text-2xl font-bold text-gray-900">PDF to Word</h2>
        <p class="text-sm text-gray-500">Convert PDF to editable Word document</p>
      </div>
    </div>

    <div class="space-y-6">
      <div v-if="!resultBlob" class="bg-white rounded-xl shadow-sm border p-6">
        <FileUpload
          ref="fileUpload"
          accept=".pdf"
          accept-text="PDF files"
          @update:files="(f) => (files = f)"
        />
        <div class="mt-4">
          <DownloadButton
            :loading="loading"
            :disabled="files.length === 0"
            @click="convert"
          >
            Convert to DOCX
          </DownloadButton>
        </div>
      </div>

      <ResultCard
        v-if="resultBlob"
        title="PDF Converted to Word"
        subtitle="Editable DOCX document ready"
        :filename="`${originalName}.docx`"
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
import FileUpload from "../components/FileUpload.vue";
import DownloadButton from "../components/DownloadButton.vue";
import ResultCard from "../components/ResultCard.vue";

const files = ref([]);
const loading = ref(false);
const error = ref("");
const fileUpload = ref(null);
const resultBlob = ref(null);
const originalName = ref("converted");

async function convert() {
  loading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    form.append("file", files.value[0]);
    originalName.value = files.value[0].name.replace(/\.pdf$/i, "");
    const res = await api.post("/convert/pdf-to-word", form, { responseType: "blob" });
    resultBlob.value = res.data;
  } catch (e) {
    error.value = e.response?.data?.detail || "Conversion failed";
  } finally {
    loading.value = false;
  }
}

function reset() {
  resultBlob.value = null;
  originalName.value = "converted";
  files.value = [];
  error.value = "";
  if (fileUpload.value) fileUpload.value.clear();
}
</script>
