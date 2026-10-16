<template>
  <div class="max-w-4xl mx-auto">
    <h2 class="text-2xl font-bold text-gray-900 mb-2">Compress PDF</h2>
    <p class="text-sm text-gray-500 mb-6">Reduce your PDF file size with image recompression and metadata cleanup.</p>

    <div class="space-y-8">
      <div v-if="!resultBlob" class="bg-white rounded-xl shadow-sm border p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center">
            <svg class="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
          </div>
          <div>
            <h3 class="font-semibold text-gray-800">Upload & Compress</h3>
            <p class="text-xs text-gray-500">Select a PDF and choose compression level</p>
          </div>
        </div>

        <FileUpload
          ref="compressUpload"
          accept=".pdf"
          accept-text="PDF files"
          @update:files="(f) => (compressFiles = f)"
        />

        <div v-if="compressFiles.length > 0" class="mt-4 flex items-center gap-2 text-sm text-gray-600">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {{ compressFiles[0].name }} ({{ formatSize(compressFiles[0].size) }})
        </div>

        <div class="mt-6">
          <label class="block text-sm font-medium text-gray-700 mb-3">Compression Level</label>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <label
              v-for="q in qualityOptions"
              :key="q.value"
              class="relative cursor-pointer"
            >
              <input
                v-model="quality"
                type="radio"
                :value="q.value"
                class="peer sr-only"
              />
              <div class="border-2 rounded-lg p-3 text-center transition-all peer-checked:border-indigo-500 peer-checked:bg-indigo-50 hover:border-gray-300">
                <div class="text-sm font-medium text-gray-800">{{ q.label }}</div>
                <div class="text-xs text-gray-500 mt-1">{{ q.desc }}</div>
                <div v-if="q.warn" class="text-xs text-amber-600 mt-1 font-medium">{{ q.warn }}</div>
              </div>
            </label>
          </div>
        </div>

        <div class="mt-6">
          <DownloadButton
            :loading="loading"
            :disabled="compressFiles.length === 0"
            @click="compressPdf"
          >
            {{ loading ? "Compressing..." : "Compress PDF" }}
          </DownloadButton>
        </div>

        <div v-if="loading" class="mt-4">
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div class="bg-indigo-600 h-2 rounded-full animate-pulse" style="width: 100%"></div>
          </div>
          <p class="text-xs text-gray-500 mt-2">Processing PDF — Ghostscript recompressing and downsampling...</p>
        </div>
      </div>

      <ResultCard
        v-if="resultBlob && stats"
        title="Compression Complete"
        :subtitle="`Using ${stats.engine === 'ghostscript' ? 'Ghostscript' : 'PikePDF'} engine`"
        :filename="`compressed_${compressFiles[0]?.name || 'output.pdf'}`"
        :file-size="resultBlob.size"
        :blob="resultBlob"
        :show-reset="true"
        @reset="reset"
      >
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <div class="text-xs text-gray-500 mb-1">Original</div>
            <div class="text-lg font-semibold text-gray-800">{{ formatSize(stats.original_size) }}</div>
          </div>
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <div class="text-xs text-gray-500 mb-1">Compressed</div>
            <div class="text-lg font-semibold text-gray-800">{{ formatSize(stats.compressed_size) }}</div>
          </div>
          <div class="text-center p-4 rounded-lg" :class="stats.reduction_percent > 0 ? 'bg-green-50' : 'bg-gray-50'">
            <div class="text-xs text-gray-500 mb-1">Reduced</div>
            <div class="text-lg font-semibold" :class="stats.reduction_percent > 0 ? 'text-green-700' : 'text-gray-600'">
              {{ stats.reduction_percent > 0 ? stats.reduction_percent + '%' : 'No change' }}
            </div>
          </div>
          <div v-if="stats.images_compressed > 0" class="text-center p-4 bg-blue-50 rounded-lg">
            <div class="text-xs text-gray-500 mb-1">Images Processed</div>
            <div class="text-lg font-semibold text-blue-700">{{ stats.images_compressed }}/{{ stats.total_images }}</div>
          </div>
        </div>
      </ResultCard>

      <div v-if="error" class="bg-red-50 text-red-700 rounded-lg p-4 text-sm">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import api from "../api";
import { getErrorMessage } from "../utils/errors";
import { formatSize } from "../utils/format";
import FileUpload from "../components/FileUpload.vue";
import DownloadButton from "../components/DownloadButton.vue";
import ResultCard from "../components/ResultCard.vue";

const compressFiles = ref([]);
const quality = ref("medium");
const loading = ref(false);
const error = ref("");
const stats = ref(null);
const compressUpload = ref(null);
const resultBlob = ref(null);

const qualityOptions = [
  { value: "extreme", label: "Extreme", desc: "72 dpi, smallest file size", warn: "May reduce readability" },
  { value: "low", label: "Low", desc: "150 dpi, good balance" },
  { value: "medium", label: "Balanced", desc: "300 dpi, print quality" },
  { value: "high", label: "High Quality", desc: "300 dpi, no subsampling" },
];

async function compressPdf() {
  loading.value = true;
  error.value = "";
  stats.value = null;
  try {
    const form = new FormData();
    form.append("file", compressFiles.value[0]);
    form.append("quality", quality.value);
    const res = await api.post("/compress", form, { responseType: "blob" });
    resultBlob.value = res.data;
    stats.value = {
      original_size: parseInt(res.headers["x-original-size"]),
      compressed_size: parseInt(res.headers["x-compressed-size"]),
      reduction_percent: parseFloat(res.headers["x-reduction-percent"]),
      images_compressed: parseInt(res.headers["x-images-compressed"] || "0"),
      total_images: parseInt(res.headers["x-total-images"] || "0"),
      engine: res.headers["x-engine"] || "unknown",
    };
  } catch (e) {
    error.value = await getErrorMessage(e, "Compression failed");
  } finally {
    loading.value = false;
  }
}

function reset() {
  resultBlob.value = null;
  stats.value = null;
  compressFiles.value = [];
  error.value = "";
  if (compressUpload.value) compressUpload.value.clear();
}
</script>
