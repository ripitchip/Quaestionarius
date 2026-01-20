import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";

// Global Styles & Fonts
import "./style.css";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/700.css";

// Lazy-load pages for better desktop performance
const routes = [
    {
        path: "/",
        name: "home",
        component: () => import("./pages/Home.vue")
    },
    {
        path: "/chat",
        name: "chat",
        component: () => import("./pages/Chat.vue")
    },
    {
        path: "/calendar",
        name: "calendar",
        component: () => import("./pages/Calendar.vue")
    },
    {
        path: "/phone",
        name: "phone",
        component: () => import("./pages/Phone.vue")
    },
    {
        path: "/settings",
        name: "settings",
        component: () => import("./pages/Settings.vue")
    },
];

const router = createRouter({
    // Use WebHistory for modern Tauri apps
    history: createWebHistory(),
    routes,
});

// Create and mount the app
const app = createApp(App);
app.use(router);
app.mount("#app");