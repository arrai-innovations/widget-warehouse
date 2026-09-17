<script setup>
import TheBreadcrumb from "./TheBreadcrumb.vue";
import TheNav from "./TheNav.vue";
import { PhCloudMoon, PhList, PhSun } from "@phosphor-icons/vue";
import Button from "@vueda/controls/button/Button.vue";
import Sonner from "@vueda/feedback/toast/Sonner.vue";
import SidebarInset from "@vueda/navigation/sidebar/SidebarInset.vue";
import SidebarProvider from "@vueda/navigation/sidebar/SidebarProvider.vue";
import SidebarTrigger from "@vueda/navigation/sidebar/SidebarTrigger.vue";
import PageTitle from "@vueda/shell/page-title/PageTitle.vue";
import StickyStackProvider from "@vueda/shell/sticky/StickyStackProvider.vue";
import { storeDarkMode } from "@vueda/stores/storeDarkMode.js";
import { usePageTitle } from "@vueda/use/usePageTitle.js";
import throttle from "lodash-es/throttle.js";
import { computed, onMounted, toRef, watch } from "vue";
import { RouterView, useRoute } from "vue-router";

import NavLogo from "@/nav/NavLogo.vue";

// Establish the page-title context above both PageTitle and the routed views, so each view can
// contribute its title via usePageTitle and its page actions via PageActions.
const pageTitle = usePageTitle().current;
const pageTitleTheme = {
    PageTitle: {
        root: { class: "bg-background" },
        titleContainer: { class: { "px-5": false, "px-4": true } },
        title: {
            class: {
                "text-[22px]": false,
                "leading-[1.2]": false,
                "tracking-[-0.005em]": false,
                "text-xl leading-tight tracking-tight": true,
            },
        },
    },
};

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
            class="absolute inset-x-0 top-0 z-10 flex h-12 items-center justify-between gap-2 border-b-hairline bg-sidebar px-4"
        >
            <NavLogo class="min-w-0 whitespace-nowrap" />
            <Button emphasis="ghost" size="icon-sm" aria-label="Toggle color mode" @click="darkModeStore.toggle()">
                <PhSun v-if="darkModeStore.isDark" weight="duotone" />
                <PhCloudMoon v-else weight="duotone" />
            </Button>
        </header>
        <RouterView />
    </div>
    <SidebarProvider v-else>
        <TheNav />
        <SidebarInset>
            <header class="flex h-12 shrink-0 items-center gap-2 border-b-hairline bg-sidebar px-4">
                <SidebarTrigger>
                    <template #icon>
                        <PhList weight="duotone" />
                    </template>
                </SidebarTrigger>
                <NavLogo class="md:hidden" />
                <div class="hidden md:block">
                    <TheBreadcrumb />
                </div>
            </header>
            <div class="border-b-hairline bg-background px-4 py-2 md:hidden">
                <TheBreadcrumb />
            </div>
            <StickyStackProvider>
                <template #top>
                    <PageTitle v-if="pageTitle.title || pageTitle.loading" :theme-override="pageTitleTheme" />
                </template>
                <RouterView />
            </StickyStackProvider>
        </SidebarInset>
    </SidebarProvider>
    <Sonner />
</template>
