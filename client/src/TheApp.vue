<script setup>
import TheNav from "./TheNav.vue";
import { faBars } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import Sonner from "@vueda/feedback/toast/Sonner.vue";
import SidebarInset from "@vueda/navigation/sidebar/SidebarInset.vue";
import SidebarProvider from "@vueda/navigation/sidebar/SidebarProvider.vue";
import SidebarTrigger from "@vueda/navigation/sidebar/SidebarTrigger.vue";
import { storeDarkMode } from "@vueda/stores/storeDarkMode.js";
import throttle from "lodash-es/throttle.js";
import { onMounted, toRef, watch } from "vue";
import { RouterView } from "vue-router";

import NavLogo from "@/nav/NavLogo.vue";

const darkModeStore = storeDarkMode();
const removeNoTransition = () => {
    document.documentElement.classList.remove("!no-transition", "[&_*]:!no-transition");
};
const throttledRemoveNoTransition = throttle(removeNoTransition, 150, {
    leading: false,
    trailing: true,
});
watch(toRef(darkModeStore, "isDark"), (isDark) => {
    document.documentElement.classList.add("!no-transition", "[&_*]:!no-transition");
    if (isDark) {
        document.documentElement.classList.add("dark");
    } else {
        document.documentElement.classList.remove("dark");
    }
    throttledRemoveNoTransition();
});
onMounted(() => {
    darkModeStore.init();
    if (darkModeStore.isDark) {
        document.documentElement.classList.add("dark");
    }
    throttledRemoveNoTransition();
});
</script>

<template>
    <SidebarProvider>
        <TheNav />
        <SidebarInset>
            <header class="flex h-12 items-center gap-2 px-4 md:hidden border-b bg-sidebar">
                <SidebarTrigger>
                    <template #icon>
                        <FontAwesomeIcon :icon="faBars" fixed-width />
                    </template>
                </SidebarTrigger>
                <NavLogo />
            </header>
            <RouterView />
        </SidebarInset>
    </SidebarProvider>
    <Sonner />
</template>
