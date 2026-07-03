<script setup>
import TheBreadcrumb from "./TheBreadcrumb.vue";
import TheNav from "./TheNav.vue";
import ThePageTitle from "./ThePageTitle.vue";
import { faBars, faCloudMoon, faSunBright } from "@fortawesome/sharp-duotone-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import Button from "@vueda/controls/button/Button.vue";
import Sonner from "@vueda/feedback/toast/Sonner.vue";
import SidebarInset from "@vueda/navigation/sidebar/SidebarInset.vue";
import SidebarProvider from "@vueda/navigation/sidebar/SidebarProvider.vue";
import SidebarTrigger from "@vueda/navigation/sidebar/SidebarTrigger.vue";
import StickyStackProvider from "@vueda/shell/sticky/StickyStackProvider.vue";
import { storeDarkMode } from "@vueda/stores/storeDarkMode.js";
import { usePageTitle } from "@vueda/use/usePageTitle.js";
import throttle from "lodash-es/throttle.js";
import { computed, onMounted, toRef, watch } from "vue";
import { RouterView, useRoute } from "vue-router";

import NavLogo from "@/nav/NavLogo.vue";

// Establish the page-title context above both ThePageTitle and the routed views, so each view can
// contribute its title via usePageTitle and its page actions via PageActions.
usePageTitle();

// Guest routes have no nav to show and nothing to break out of, so they skip the sidebar shell while
// keeping a small amount of public chrome for branding and global controls.
const route = useRoute();
const isGuestRoute = computed(() => route.meta.guest === true);

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
    <div v-if="isGuestRoute" class="relative min-h-svh bg-background text-foreground">
        <header
            class="absolute inset-x-0 top-0 z-10 flex h-12 items-center justify-between gap-2 border-b bg-sidebar px-4"
        >
            <NavLogo class="min-w-0 whitespace-nowrap" />
            <Button emphasis="ghost" size="icon-sm" aria-label="Toggle color mode" @click="darkModeStore.toggle()">
                <FontAwesomeIcon :icon="darkModeStore.isDark ? faSunBright : faCloudMoon" fixed-width />
            </Button>
        </header>
        <RouterView />
    </div>
    <SidebarProvider v-else>
        <TheNav />
        <SidebarInset>
            <header class="flex h-12 shrink-0 items-center gap-2 border-b bg-sidebar px-4">
                <SidebarTrigger>
                    <template #icon>
                        <FontAwesomeIcon :icon="faBars" fixed-width />
                    </template>
                </SidebarTrigger>
                <NavLogo class="md:hidden" />
                <div class="hidden md:block">
                    <TheBreadcrumb />
                </div>
            </header>
            <div class="border-b bg-background px-4 py-2 md:hidden">
                <TheBreadcrumb />
            </div>
            <StickyStackProvider>
                <template #top>
                    <ThePageTitle />
                </template>
                <RouterView />
            </StickyStackProvider>
        </SidebarInset>
    </SidebarProvider>
    <Sonner />
</template>
