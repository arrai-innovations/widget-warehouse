<script setup>
import LoadingSpinnerInline from "@vueda/display/loading/LoadingSpinnerInline.vue";
import { usePageTitle } from "@vueda/use/usePageTitle.js";
import { computed, ref } from "vue";

/**
 * Widget Warehouse's own page-title display.
 *
 * This is a worked example of the "build a custom title display" pattern from VUEDA's
 * "Place the Page Title and Page Actions" guide. Rather than dropping in VUEDA's stock
 * `PageTitle`, we own the markup so the header reads as part of our shell.
 *
 * `TheApp` establishes the page-title context above both this display and `<RouterView>`,
 * so the no-argument `usePageTitle()` call here reuses that context: views contribute
 * their title and loading state, and `PageActions` teleports view buttons into the zone
 * we bind below.
 */
const page = usePageTitle();
const title = computed(() => page.current.value.title);
const loading = computed(() => page.current.value.loading);

// The element page actions teleport into. Bind the ref so it resolves once mounted.
const actionZone = ref(null);
page.bindActionZone(actionZone);
</script>

<template>
    <header
        v-if="title || loading"
        class="flex items-baseline justify-between gap-2 border-b-hairline bg-background px-4 py-3 md:gap-4"
    >
        <div class="flex items-center gap-2">
            <h1 class="text-xl font-semibold leading-tight tracking-tight">
                {{ title }}
            </h1>
            <span class="flex size-5 shrink-0 items-center justify-center text-base" data-qa="page-title-loading">
                <LoadingSpinnerInline v-if="loading" />
            </span>
        </div>
        <!-- PageActions teleports the active view's buttons here. -->
        <div ref="actionZone" class="flex flex-wrap justify-end gap-1 self-center" data-qa="page-title-actions" />
    </header>
</template>
