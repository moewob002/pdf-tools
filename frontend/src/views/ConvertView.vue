<template>
  <div class="max-w-4xl mx-auto">
    <h2 class="text-2xl font-bold text-gray-900 mb-2">Convert PDF</h2>
    <p class="text-sm text-gray-500 mb-6">Transform your PDF files to and from other formats.</p>

    <div class="space-y-8">
      <!-- PDF to Images -->
      <div v-if="!pdfToImgBlob" class="bg-white rounded-xl shadow-sm border p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
            <svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <h3 class="font-semibold text-gray-800">PDF to Images</h3>
            <p class="text-xs text-gray-500">Extract each page as an image file</p>
          </div>
        </div>
        <FileUpload
          ref="pdfToImgUpload"
          accept=".pdf"
          accept-text="PDF files"
          @update:files="onPdfToImgChange"
        />
        <div v-if="pdfToImgPreview.length > 0" class="mt-4">
          <p class="text-xs text-gray-500 mb-2">{{ pdfToImgPreview.length }} pages will be converted</p>
          <div class="flex gap-2 overflow-x-auto pb-2">
            <div
              v-for="page in pdfToImgPreview.slice(0, 8)"
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
              v-if="pdfToImgPreview.length > 8"
              class="flex-shrink-0 h-24 w-16 rounded border bg-gray-50 flex items-center justify-center text-xs text-gray-500"
            >
              +{{ pdfToImgPreview.length - 8 }} more
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
            :disabled="pdfToImgFiles.length === 0"
            @click="convertPdfToImage"
          >
            Convert to Images
          </DownloadButton>
        </div>
      </div>

      <ResultCard
        v-if="pdfToImgBlob"
        title="PDF Converted to Images"
        :subtitle="`${pdfToImgPageCount} pages extracted as ${imgFormat.toUpperCase()}`"
        filename="images.zip"
        :file-size="pdfToImgBlob.size"
        :blob="pdfToImgBlob"
        :show-reset="true"
        @reset="resetPdfToImg"
      />

      <!-- Images to PDF -->
      <div v-if="!imgToPdfBlob" class="bg-white rounded-xl shadow-sm border p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
            <svg class="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h3 class="font-semibold text-gray-800">Images to PDF</h3>
            <p class="text-xs text-gray-500">Combine multiple images into a single PDF</p>
          </div>
        </div>
        <FileUpload
          ref="imgToPdfUpload"
          accept="image/*"
          accept-text="PNG, JPG, TIFF, BMP images"
          :multiple="true"
          @update:files="(f) => (imgToPdfFiles = f)"
        />
        <div v-if="imgToPdfFiles.length > 0" class="mt-4">
          <p class="text-xs text-gray-500">{{ imgToPdfFiles.length }} image{{ imgToPdfFiles.length !== 1 ? 's' : '' }} will be combined</p>
        </div>
        <div class="mt-4">
          <DownloadButton
            :loading="loading"
            :disabled="imgToPdfFiles.length === 0"
            @click="convertImagesToPdf"
          >
            Convert to PDF
          </DownloadButton>
        </div>
      </div>

      <ResultCard
        v-if="imgToPdfBlob"
        title="Images Converted to PDF"
        :subtitle="`${imgToPdfCount} images combined into one PDF`"
        filename="converted.pdf"
        :file-size="imgToPdfBlob.size"
        :blob="imgToPdfBlob"
        :show-reset="true"
        @reset="resetImgToPdf"
      />

      <!-- PDF to Word -->
      <div v-if="!pdfToWordBlob" class="bg-white rounded-xl shadow-sm border p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
            <svg class="w-5 h-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h3 class="font-semibold text-gray-800">PDF to Word</h3>
            <p class="text-xs text-gray-500">Convert PDF to editable Word document</p>
          </div>
        </div>
        <FileUpload
          ref="pdfToWordUpload"
          accept=".pdf"
          accept-text="PDF files"
          @update:files="(f) => (pdfToWordFiles = f)"
        />
        <div class="mt-4">
          <DownloadButton
            :loading="loading"
            :disabled="pdfToWordFiles.length === 0"
            @click="convertPdfToWord"
          >
            Convert to DOCX
          </DownloadButton>
        </div>
      </div>

      <ResultCard
        v-if="pdfToWordBlob"
        title="PDF Converted to Word"
        subtitle="Editable DOCX document ready"
        filename="converted.docx"
        :file-size="pdfToWordBlob.size"
        :blob="pdfToWordBlob"
        :show-reset="true"
        @reset="resetPdfToWord"
      />

      <div v-if="error" class="bg-red-50 text-red-700 rounded-lg p-4 text-sm">
        {{ error }}
      </div>
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

const pdfToImgFiles = ref([]);
const pdfToImgPreview = ref([]);
const imgToPdfFiles = ref([]);
const pdfToWordFiles = ref([]);
const imgFormat = ref("png");
const dpi = ref(200);
const loading = ref(false);
const error = ref("");
const pdfToImgUpload = ref(null);
const imgToPdfUpload = ref(null);
const pdfToWordUpload = ref(null);

const pdfToImgBlob = ref(null);
const pdfToImgPageCount = ref(0);
const imgToPdfBlob = ref(null);
const imgToPdfCount = ref(0);
const pdfToWordBlob = ref(null);

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

async function onPdfToImgChange(files) {
  pdfToImgFiles.value = files;
  pdfToImgPreview.value = [];
  if (files.length > 0) {
    try {
      const form = new FormData();
      form.append("file", files[0]);
      form.append("dpi", "72");
      const res = await api.post("/edit/thumbnails", form);
      pdfToImgPreview.value = res.data.pages;
    } catch (_) {}
  }
}

async function convertPdfToImage() {
  loading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    form.append("file", pdfToImgFiles.value[0]);
    form.append("format", imgFormat.value);
    form.append("dpi", dpi.value);
    const res = await api.post("/convert/pdf-to-image", form, {
      responseType: "blob",
    });
    pdfToImgBlob.value = res.data;
    pdfToImgPageCount.value = pdfToImgPreview.value.length || 0;
  } catch (e) {
    error.value = e.response?.data?.detail || "Conversion failed";
  } finally {
    loading.value = false;
  }
}

async function convertImagesToPdf() {
  loading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    imgToPdfFiles.value.forEach((f) => form.append("files", f));
    const res = await api.post("/convert/image-to-pdf", form, {
      responseType: "blob",
    });
    imgToPdfBlob.value = res.data;
    imgToPdfCount.value = imgToPdfFiles.value.length;
  } catch (e) {
    error.value = e.response?.data?.detail || "Conversion failed";
  } finally {
    loading.value = false;
  }
}

async function convertPdfToWord() {
  loading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    form.append("file", pdfToWordFiles.value[0]);
    const res = await api.post("/convert/pdf-to-word", form, {
      responseType: "blob",
    });
    pdfToWordBlob.value = res.data;
  } catch (e) {
    error.value = e.response?.data?.detail || "Conversion failed";
  } finally {
    loading.value = false;
  }
}

function resetPdfToImg() {
  pdfToImgBlob.value = null;
  pdfToImgPageCount.value = 0;
  pdfToImgFiles.value = [];
  pdfToImgPreview.value = [];
  if (pdfToImgUpload.value) pdfToImgUpload.value.clear();
}

function resetImgToPdf() {
  imgToPdfBlob.value = null;
  imgToPdfCount.value = 0;
  imgToPdfFiles.value = [];
  if (imgToPdfUpload.value) imgToPdfUpload.value.clear();
}

function resetPdfToWord() {
  pdfToWordBlob.value = null;
  pdfToWordFiles.value = [];
  if (pdfToWordUpload.value) pdfToWordUpload.value.clear();
}
</script>
