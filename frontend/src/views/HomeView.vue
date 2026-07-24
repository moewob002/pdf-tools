<template>
  <div class="max-w-4xl mx-auto py-12">
    <div class="text-center mb-12">
      <h1 class="text-4xl font-bold text-gray-900 mb-3">PDF Tools</h1>
      <p class="text-lg text-gray-500 max-w-xl mx-auto">
        Convert, edit, OCR, and compress your PDF files.
        Everything runs locally — your files never leave the server.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <router-link
        v-for="tool in tools"
        :key="tool.path"
        :to="tool.path"
        class="group bg-white rounded-xl shadow-sm border p-6 hover:shadow-md hover:border-indigo-300 transition-all"
      >
        <div class="flex items-start gap-4">
          <div
            class="w-12 h-12 rounded-xl flex items-center justify-center transition-colors"
            :class="tool.bgColor"
          >
            <component :is="tool.icon" class="w-6 h-6" :class="tool.iconColor" />
          </div>
          <div class="flex-1">
            <h3 class="text-lg font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors">
              {{ tool.title }}
            </h3>
            <p class="text-sm text-gray-500 mt-1">{{ tool.desc }}</p>
            <div class="flex flex-wrap gap-2 mt-3">
              <span
                v-for="tag in tool.tags"
                :key="tag"
                class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full"
              >
                {{ tag }}
              </span>
            </div>
          </div>
          <svg
            class="w-5 h-5 text-gray-300 group-hover:text-indigo-400 transition-colors mt-1"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { h } from "vue";

const tools = [
  {
    path: "/convert/pdf-to-image",
    title: "PDF to Images",
    desc: "Extract each page as an image file",
    tags: ["PNG", "JPG", "TIFF"],
    bgColor: "bg-blue-50",
    iconColor: "text-blue-600",
    icon: {
      render() {
        return h("svg", { fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
          h("path", {
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            "stroke-width": "2",
            d: "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z",
          }),
        ]);
      },
    },
  },
  {
    path: "/convert/image-to-pdf",
    title: "Images to PDF",
    desc: "Combine multiple images into a single PDF",
    tags: ["PNG", "JPG", "BMP"],
    bgColor: "bg-green-50",
    iconColor: "text-green-600",
    icon: {
      render() {
        return h("svg", { fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
          h("path", {
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            "stroke-width": "2",
            d: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
          }),
        ]);
      },
    },
  },
  {
    path: "/convert/pdf-to-word",
    title: "PDF to Word",
    desc: "Convert PDF to editable Word document",
    tags: ["DOCX", "Text Extract"],
    bgColor: "bg-purple-50",
    iconColor: "text-purple-600",
    icon: {
      render() {
        return h("svg", { fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
          h("path", {
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            "stroke-width": "2",
            d: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
          }),
        ]);
      },
    },
  },
  {
    path: "/edit",
    title: "Edit",
    desc: "Split, merge, and manage PDF pages",
    tags: ["Split", "Merge", "Delete Pages"],
    bgColor: "bg-amber-50",
    iconColor: "text-amber-600",
    icon: {
      render() {
        return h("svg", { fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
          h("path", {
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            "stroke-width": "2",
            d: "M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4",
          }),
        ]);
      },
    },
  },
  {
    path: "/ocr",
    title: "OCR",
    desc: "Extract text from scanned PDF documents",
    tags: ["Multi-language", "Tesseract", "Text Extraction"],
    bgColor: "bg-indigo-50",
    iconColor: "text-indigo-600",
    icon: {
      render() {
        return h("svg", { fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
          h("path", {
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            "stroke-width": "2",
            d: "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
          }),
        ]);
      },
    },
  },
  {
    path: "/compress",
    title: "Compress",
    desc: "Reduce PDF file size while maintaining quality",
    tags: ["Low", "Medium", "High Quality"],
    bgColor: "bg-rose-50",
    iconColor: "text-rose-600",
    icon: {
      render() {
        return h("svg", { fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
          h("path", {
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            "stroke-width": "2",
            d: "M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4",
          }),
        ]);
      },
    },
  },
];
</script>
