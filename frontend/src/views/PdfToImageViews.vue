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
        <h2 class="text-2xl font-bold text-gray-900">PDF to Images</h2>
        <p class="text-sm text-gray-500">Extract each page as an image file</p>
      </div>
    </div>

    <div class="space-y-6">
      <div v-if="!resultBlob" class="bg-white rounded-xl shadow-sm border p-6">
        <FileUpload
          ref="fileUpload"
          accept=".pdf"
          accept-text="PDF files"
          @update:files="onFileChange"
        />

        <div v-if="preview.length > 0" class="mt-4">
          <p class="text-xs text-gray-500 mb-2">{{ preview.length }} pages will be converted</p>
          <div class="flex gap-2 overflow-x-auto pb-2">
            <div
              v-for="page in preview.slice(0, 8)"
              :key="page.page"
              class="flex-shrink-0 relative group/thumb cursor-pointer"
              @click="openPreview(page, `Page ${page.page}`)"
            >
              <img
                :src="'data:image/jpeg;base64,' + page.image"
                class="h-24 rounded border"
              />
              <div class="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-[10px] text-center py-0.5 rounded-b">
                {{ page.page }}
              </div>
            </div>
            <div
              v-if="preview.length > 8"
              class="flex-shrink-0 h-24 w-16 rounded border bg-gray-50 flex items-center justify-center text-xs text-gray-500"
            >
              +{{ preview.length - 8 }} more
            </div>
          </div>
        </div>

        <div class="mt-4 flex items-center gap-4">
          <select v-model="imgFormat" class="border rounded-lg px-3 py-2 text-sm">
            <option value="png">PNG</option>
            <option value="jpg">JPG</option>
            <option value="tiff">TIFF</option>
          </select>
          <select v-model="dpi" class="border rounded-lg px-3 py-2 text-sm">
            <option :value="150">150 DPI</option>
            <option :value="200">200 DPI</option>
            <option :value="300">300 DPI</option>
          </select>
          <DownloadButton
            :loading="loading"
            :disabled="files.length === 0"
            @click="convert"
          >
            Convert to Images
          </DownloadButton>
        </div>
      </div>

      <ResultCard
        v-if="resultBlob"
        title="PDF Converted to Images"
        :subtitle="`${pageCount} pages extracted as ${imgFormat.toUpperCase()}`"
        filename="images.zip"
        :file-size="resultBlob.size"
        :blob="resultBlob"
        :show-reset="true"
        @reset="reset"
      />

      <div v-if="error" class="bg-red-50 text-red-700 rounded-lg p-4 text-sm">{{ error }}</div>
    </div>

    <ImageModal
      :show="!!previewData"
      :src="previewSrc"
      :title="previewTitle"
      @close="previewData = null"
    />
  </div>
</template>

<script setup>
import { ref, computed, defineAsyncComponent } from "vue";
import api from "../api";
import FileUpload from "../components/FileUpload.vue";
import DownloadButton from "../components/DownloadButton.vue";
import ResultCard from "../components/ResultCard.vue";

const ImageModal = defineAsyncComponent(() =>
  import("../components/ImageModal.vue")
);

const files = ref([]);
const preview = ref([]);
const imgFormat = ref("png");
const dpi = ref(200);
const loading = ref(false);
const error = ref("");
const fileUpload = ref(null);
const resultBlob = ref(null);
const pageCount = ref(0);

const previewData = ref(null);
const previewTitle = ref("");
const previewSrc = computed(() => {
  if (!previewData.value) return "";
  return "data:image/jpeg;base64," + previewData.value.image;
});

function openPreview(page, title) {
  previewData.value = page;
  previewTitle.value = title;
}

async function onFileChange(f) {
  files.value = f;
  preview.value = [];
  if (f.length > 0) {
    try {
      const form = new FormData();
      form.append("file", f[0]);
      form.append("dpi", "72");
      const res = await api.post("/edit/thumbnails", form);
      preview.value = res.data.pages;
    } catch (_) {}
  }
}

async function convert() {
  loading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    form.append("file", files.value[0]);
    form.append("format", imgFormat.value);
    form.append("dpi", dpi.value);
    const res = await api.post("/convert/pdf-to-image", form, { responseType: "blob" });
    resultBlob.value = res.data;
    pageCount.value = preview.value.length || 0;
  } catch (e) {
    error.value = e.response?.data?.detail || "Conversion failed";
  } finally {
    loading.value = false;
  }
}

function reset() {
  resultBlob.value = null;
  pageCount.value = 0;
  files.value = [];
  preview.value = [];
  error.value = "";
  if (fileUpload.value) fileUpload.value.clear();
}
</script>
