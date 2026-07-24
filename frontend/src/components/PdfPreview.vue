<template>
  <div class="bg-white rounded-lg shadow p-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-medium text-gray-700">Preview</h3>
      <div class="flex items-center space-x-2">
        <button
          class="text-gray-500 hover:text-gray-700 text-sm"
          @click="prevPage"
          :disabled="currentPage <= 1"
        >
          Prev
        </button>
        <span class="text-sm text-gray-600">
          {{ currentPage }} / {{ totalPages }}
        </span>
        <button
          class="text-gray-500 hover:text-gray-700 text-sm"
          @click="nextPage"
          :disabled="currentPage >= totalPages"
        >
          Next
        </button>
      </div>
    </div>
    <div class="border rounded overflow-hidden" ref="container">
      <canvas ref="canvas" class="w-full" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import * as pdfjsLib from "pdfjs-dist";

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url
).toString();

const props = defineProps({
  file: { type: Object, required: true },
});

const canvas = ref(null);
const container = ref(null);
const currentPage = ref(1);
const totalPages = ref(0);
let pdfDoc = null;

async function renderPage(num) {
  if (!pdfDoc) return;
  const page = await pdfDoc.getPage(num);
  const viewport = page.getViewport({ scale: 1.5 });
  const ctx = canvas.value.getContext("2d");
  canvas.value.height = viewport.height;
  canvas.value.width = viewport.width;
  await page.render({ canvasContext: ctx, viewport }).promise;
}

async function loadPdf() {
  const data = await props.file.arrayBuffer();
  pdfDoc = await pdfjsLib.getDocument({ data }).promise;
  totalPages.value = pdfDoc.numPages;
  currentPage.value = 1;
  renderPage(1);
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
    renderPage(currentPage.value);
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
    renderPage(currentPage.value);
  }
}

onMounted(loadPdf);
watch(() => props.file, loadPdf);
</script>
