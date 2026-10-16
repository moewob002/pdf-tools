<template>
  <div class="mx-auto max-w-4xl">
    <PageHeader
      :title="tool.title"
      :description="tool.desc"
      :category="tool.category"
      :icon="tool.icon"
      :back="{ path: '/edit', label: 'Edit tools' }"
    />

    <div v-if="!resultBlob" class="space-y-5">
      <ToolStep :number="1" title="Upload PDFs" hint="Add two or more files. You can add more later.">
        <FileUpload
          ref="mergeUpload"
          accept=".pdf"
          accept-text="PDF files"
          :multiple="true"
          :file-status="fileStatus"
          @update:files="onFilesChange"
        />

        <AlertMessage v-if="failedSources.length" tone="warning" title="Some files were not added" class="mt-4">
          <ul class="space-y-1">
            <li v-for="source in failedSources" :key="source.id">
              <strong>{{ source.name }}</strong>: {{ source.error }}
            </li>
          </ul>
        </AlertMessage>
      </ToolStep>

      <ToolStep :number="2" title="Arrange pages" hint="The merged PDF follows this order.">
        <MergeReorder
          v-if="mergePages.length > 0"
          v-model="mergePages"
          :loading="false"
          @addMore="triggerAddMore"
        />
        <ProcessingSpinner v-else-if="previewLoading" message="Loading page previews…" submessage="Reading each PDF" />
        <p v-else class="rounded-xl border border-dashed border-line-strong px-4 py-6 text-center text-sm text-muted">
          Pages from your PDFs appear here.
        </p>
        <p v-if="previewLoading && mergePages.length > 0" class="mt-3 text-sm text-muted" role="status">
          Still reading some files…
        </p>
      </ToolStep>

      <ToolStep :number="3" title="Merge and download">
        <div class="flex flex-wrap items-center gap-3">
          <DownloadButton
            :loading="loading"
            loading-text="Merging…"
            :disabled="mergePages.length < 2 || previewLoading"
            @click="mergePdfs"
          >
            Merge {{ mergePages.length }} Pages
          </DownloadButton>
          <p class="text-sm text-muted">
            <template v-if="previewLoading">Wait until every file has been read.</template>
            <template v-else-if="mergePages.length < 2">Add at least two pages.</template>
            <template v-else>From {{ fileCount }} file{{ fileCount !== 1 ? 's' : '' }}.</template>
          </p>
        </div>
      </ToolStep>
    </div>

    <ResultCard
      v-if="resultBlob"
      title="Merge complete"
      :subtitle="`${resultPageCount} pages merged from ${resultFileCount} file${resultFileCount !== 1 ? 's' : ''}`"
      filename="merged.pdf"
      :file-size="resultBlob.size"
      :blob="resultBlob"
      :show-reset="true"
      @reset="reset"
    />

    <AlertMessage v-if="error" class="mt-5">{{ error }}</AlertMessage>
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
import AlertMessage from "../components/AlertMessage.vue";
import PageHeader from "../components/PageHeader.vue";
import ToolStep from "../components/ToolStep.vue";
import { toolById } from "../tools";

const MergeReorder = defineAsyncComponent(() =>
  import("../components/MergeReorder.vue")
);

const tool = toolById("merge");

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

function fileStatus(file) {
  const source = sources.value.find((s) => s.file === file);
  if (!source || source.status === "loading") return { state: "loading", label: "Reading…" };
  if (source.status === "error") return { state: "error", label: "Not added" };
  const pages = mergePages.value.filter((p) => p.file_index === source.id).length;
  return { state: "ready", label: `${pages} page${pages !== 1 ? "s" : ""}` };
}

function updateSource(id, patch) {
  sources.value = sources.value.map((s) => (s.id === id ? { ...s, ...patch } : s));
}

function triggerAddMore() {
  mergeUpload.value?.openPicker();
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
