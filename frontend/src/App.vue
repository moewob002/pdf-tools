<template>
  <div class="flex min-h-screen flex-col">
    <a
      href="#main"
      class="sr-only-focusable fixed left-4 top-3 z-50 rounded-lg bg-surface px-4 py-2 text-sm font-semibold text-primary-text shadow-md"
    >
      Skip to content
    </a>

    <header class="sticky top-0 z-40 border-b border-line bg-surface/90 backdrop-blur supports-[backdrop-filter]:bg-surface/80">
      <div class="mx-auto flex max-w-5xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2.5 sm:px-6">
        <router-link to="/" class="flex items-center gap-2.5 rounded-lg font-bold text-fg">
          <span class="inline-flex h-9 w-9 items-center justify-center rounded-xl text-on-primary shadow-md" style="background-image: var(--gradient-brand)">
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 0 0 2-2V9.4a1 1 0 0 0-.3-.7l-5.4-5.4a1 1 0 0 0-.7-.3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2zM9 13h6M9 17h4" />
            </svg>
          </span>
          <span class="text-lg tracking-tight">PDF Tools</span>
        </router-link>

        <div class="order-2 ml-auto sm:order-3 sm:ml-0">
          <ThemeToggle />
        </div>

        <nav aria-label="Tools" class="order-3 w-full sm:order-2 sm:ml-auto sm:w-auto">
          <ul class="grid grid-cols-4 gap-1 sm:flex">
            <li v-for="link in navLinks" :key="link.path">
              <router-link
                :to="link.path"
                class="block rounded-xl px-3 py-2 text-center text-sm font-semibold transition-colors"
                :class="isActive(link.path) ? 'text-on-primary shadow-md' : 'text-muted hover:bg-surface-2 hover:text-fg'"
                :style="isActive(link.path) ? { backgroundImage: 'var(--gradient-brand)' } : null"
                :aria-current="isActive(link.path) ? 'page' : undefined"
              >
                {{ link.name }}
              </router-link>
            </li>
          </ul>
        </nav>
      </div>
    </header>

    <main id="main" tabindex="-1" class="flex-1 px-4 py-8 focus:outline-none sm:px-6 sm:py-10">
      <router-view />
    </main>

    <footer class="border-t border-line px-4 py-6 text-center text-xs text-muted sm:px-6">
      Files are processed on this server only and deleted as soon as each result has been sent to you.
    </footer>
  </div>
</template>

<script setup>
import { useRoute } from "vue-router";
import ThemeToggle from "./components/ThemeToggle.vue";

const route = useRoute();

const navLinks = [
  { path: "/convert", name: "Convert" },
  { path: "/edit", name: "Edit" },
  { path: "/ocr", name: "OCR" },
  { path: "/compress", name: "Compress" },
];

function isActive(path) {
  return route.path === path || route.path.startsWith(path + "/");
}
</script>
