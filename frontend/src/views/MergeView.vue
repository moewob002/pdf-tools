<template>
  <div class="max-w-4xl mx-auto">
    <div class="flex items-center gap-3 mb-6">
      <router-link
        to="/edit"
        class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </router-link>
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Merge PDFs</h2>
        <p class="text-sm text-gray-500">Combine pages from multiple PDFs, drag to reorder</p>
      </div>
    </div>

    <div class="space-y-6">
      <div v-if="!resultBlob" class="bg-white rounded-xl shadow-sm border p-6">
        <FileUpload
          ref="mergeUpload"
          accept=".pdf"
          accept-text="PDF files"
          :multiple="true"
          @update:files="onFilesChange"
        />

        <ul v-if="failedSources.length" class="mt-4 space-y-2">
          <li
            v-for="source in failedSources"
            :key="source.id"
            class="bg-red-50 text-red-700 rounded-lg p-3 text-sm"
          >
            <strong>{{ source.name }}</strong> was not added: {{ source.error }}
          </li>
        </ul>

        <div v-if="previewLoading" class="mt-4">
          <ProcessingSpinner message="Loading page previews..." submessage="Extracting thumbnails from each PDF" />
        </div>

        <div v-if="mergePages.length > 0" class="mt-4">
          <MergeReorder
            v-model="mergePages"
            :loading="false"
            @addMore="triggerAddMore"
          />
          <div class="mt-4 flex items-center gap-4">
            <DownloadButton
              :loading="loading"
              :disabled="mergePages.length < 2 || previewLoading"
              @click="mergePdfs"
            >
              Merge {{ mergePages.length }} Pages
            </DownloadButton>
            <span class="text-xs text-gray-500">from {{ fileCount }} file{{ fileCount !== 1 ? 's' : '' }}</span>
          </div>
        </div>
      </div>

      <ResultCard
        v-if="resultBlob"
        title="Merge Complete"
        :subtitle="`${resultPageCount} pages merged from ${resultFileCount} file${resultFileCount !== 1 ? 's' : ''}`"
        filename="merged.pdf"
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
import { ref, computed, defineAsyncComponent } from "vue";
import api from "../api";
import { loadThumbnails } from "../api/thumbnails";
import { getErrorMessage } from "../utils/errors";
import { buildMergeRequest, diffSources, withoutSources } from "../utils/merge";
import FileUpload from "../components/FileUpload.vue";
import DownloadButton from "../components/DownloadButton.vue";
import ProcessingSpinner from "../components/ProcessingSpinner.vue";
import ResultCard from "../components/ResultCard.vue";

const MergeReorder = defineAsyncComponent(() =>
  import("../components/MergeReorder.vue")
);

// One entry per uploaded file: { id, file, name, status: "loading" | "ready" | "error", error }
const sources = ref([]);
const mergePages = ref([]);
const loading = ref(false);
const error = ref("");
const mergeUpload = ref(null);
const resultBlob = ref(null);
const resultPageCount = ref(0);
const resultFileCount = ref(0);

let nextSourceId = 0;

const previewLoading = computed(() => sources.value.some((s) => s.status === "loading"));
const failedSources = computed(() => sources.value.filter((s) => s.status === "error"));
const fileCount = computed(
  () => new Set(mergePages.value.map((p) => p.file_index)).size
);

async function onFilesChange(files) {
  error.value = "";
  const { added, removedIds } = diffSources(sources.value, files);

  if (removedIds.length) {
    sources.value = sources.value.filter((s) => !removedIds.includes(s.id));
    mergePages.value = withoutSources(mergePages.value, removedIds);
  }

  // Load previews one file at a time; the backend rate-limits bursts.
  for (const file of added) {
    const source = { id: nextSourceId++, file, name: file.name, status: "loading", error: "" };
    sources.value = [...sources.value, source];
    try {
      const pages = await loadThumbnails(file);
      if (!sources.value.some((s) => s.id === source.id)) continue; // removed meanwhile
      mergePages.value = [
        ...mergePages.value,
        ...pages.map((page) => ({
          id: `${source.id}-${page.page}`,
          file_index: source.id,
          page_num: page.page,
          source_name: file.name,
          thumbnail: page.image,
        })),
      ];
      updateSource(source.id, { status: "ready" });
    } catch (e) {
      // Never guess the page count: a file whose preview failed is not added at all.
      updateSource(source.id, {
        status: "error",
        error: await getErrorMessage(e, "Could not read this PDF"),
      });
    }
  }
}

function updateSource(id, patch) {
  sources.value = sources.value.map((s) => (s.id === id ? { ...s, ...patch } : s));
}

function triggerAddMore() {
  if (mergeUpload.value?.$el) {
    const input = mergeUpload.value.$el.querySelector('input[type="file"]');
    if (input) input.click();
  }
}

async function mergePdfs() {
  loading.value = true;
  error.value = "";
  try {
    const { files, pageOrder } = buildMergeRequest(mergePages.value, sources.value);
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    form.append("page_order", JSON.stringify(pageOrder));

    const res = await api.post("/edit/merge-custom", form, { responseType: "blob" });
    resultBlob.value = res.data;
    resultPageCount.value = pageOrder.length;
    resultFileCount.value = files.length;
  } catch (e) {
    error.value = await getErrorMessage(e, "Merge failed");
  } finally {
    loading.value = false;
  }
}

function reset() {
  resultBlob.value = null;
  sources.value = [];
  mergePages.value = [];
  resultPageCount.value = 0;
  resultFileCount.value = 0;
  error.value = "";
  if (mergeUpload.value) mergeUpload.value.clear();
}
</script>
