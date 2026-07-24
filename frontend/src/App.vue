<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white border-b sticky top-0 z-40">
      <div class="max-w-5xl mx-auto px-4 sm:px-6">
        <div class="flex items-center justify-between h-14">
          <router-link
            to="/"
            class="font-bold text-indigo-600 text-lg"
          >
            PDF Tools
          </router-link>
          <div class="flex items-center gap-1">
            <router-link
              v-for="link in navLinks"
              :key="link.path"
              :to="link.path"
              class="px-3 py-1.5 text-sm font-medium rounded-lg transition-colors"
              :class="[
                isActive(link.path)
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
              ]"
            >
              {{ link.name }}
            </router-link>
          </div>
        </div>
      </div>
    </nav>
    <main class="py-8 px-4 sm:px-6">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRoute } from "vue-router";

const route = useRoute();

const navLinks = [
  { path: "/convert", name: "Convert" },
  { path: "/edit", name: "Edit" },
  { path: "/ocr", name: "OCR" },
  { path: "/compress", name: "Compress" },
];

function isActive(path) {
  if (path === "/edit") {
    return route.path.startsWith("/edit");
  }
  return route.path === path;
}
</script>
