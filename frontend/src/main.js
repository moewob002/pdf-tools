import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import "./style.css";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      component: () => import("./views/HomeView.vue"),
    },
    {
      path: "/convert/pdf-to-image",
      component: () => import("./views/PdfToImageViews.vue"),
    },
    {
      path: "/convert/image-to-pdf",
      component: () => import("./views/ImagesToPdfView.vue"),
    },
    {
      path: "/convert/pdf-to-word",
      component: () => import("./views/PdfToWordView.vue"),
    },
    {
      path: "/edit",
      component: () => import("./views/EditView.vue"),
    },
    {
      path: "/edit/split",
      component: () => import("./views/SplitView.vue"),
    },
    {
      path: "/edit/merge",
      component: () => import("./views/MergeView.vue"),
    },
    {
      path: "/edit/delete",
      component: () => import("./views/DeleteView.vue"),
    },
    {
      path: "/ocr",
      component: () => import("./views/OcrView.vue"),
    },
    {
      path: "/compress",
      component: () => import("./views/CompressView.vue"),
    },
  ],
});

const app = createApp(App);
app.use(router);
app.mount("#app");
