<script setup>
import TheNav from "./TheNav.vue";
import Sonner from "@vueda/feedback/toast/Sonner.vue";
import SidebarInset from "@vueda/navigation/sidebar/SidebarInset.vue";
import SidebarProvider from "@vueda/navigation/sidebar/SidebarProvider.vue";
import { storeDarkMode } from "@vueda/stores/storeDarkMode.js";
import { onMounted, toRef, watch } from "vue";
import { RouterView } from "vue-router";

const darkModeStore = storeDarkMode();
watch(toRef(darkModeStore, "isDark"), (isDark) => {
    if (isDark) {
        document.documentElement.classList.add("dark");
    } else {
        document.documentElement.classList.remove("dark");
    }
});
onMounted(() => {
    darkModeStore.init();
    if (darkModeStore.isDark) {
        document.documentElement.classList.add("dark");
    }
});
</script>

<template>
    <SidebarProvider>
        <TheNav />
        <SidebarInset>
            <!-- TODO: mobile nav header -->
            <RouterView />
        </SidebarInset>
    </SidebarProvider>
    <Sonner />
</template>
