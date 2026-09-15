<script setup>
import Skeleton from "@vueda/feedback/skeleton/Skeleton.vue";
import Breadcrumb from "@vueda/navigation/breadcrumb/Breadcrumb.vue";
import BreadcrumbItem from "@vueda/navigation/breadcrumb/BreadcrumbItem.vue";
import BreadcrumbLink from "@vueda/navigation/breadcrumb/BreadcrumbLink.vue";
import BreadcrumbList from "@vueda/navigation/breadcrumb/BreadcrumbList.vue";
import BreadcrumbPage from "@vueda/navigation/breadcrumb/BreadcrumbPage.vue";
import BreadcrumbSeparator from "@vueda/navigation/breadcrumb/BreadcrumbSeparator.vue";
import { getCRUDForTo } from "@vueda/router/getCrud.js";
import { storeModelInfo } from "@vueda/stores/storeModelInfo.js";
import { storeUser } from "@vueda/stores/storeUser.js";
import { memoizedStartCase } from "@vueda/utils/case.js";
import { computedAsync } from "@vueuse/core";
import { computed, unref } from "vue";
import { RouterLink, useRoute } from "vue-router";

const route = useRoute();
const modelInfoStore = storeModelInfo();
const userStore = storeUser();

// Until the initial navigation resolves, `route` is Vue Router's START_LOCATION
// (name: undefined, empty params). The CRUD `beforeEnter` guard (requireModelInfo)
// holds this window open until model info is fetched, so a null route name is our
// signal for the reload flash where we don't yet know app/model/action. It flips
// the instant the route commits, unlike router.isReady() which lags by a tick.
const routeResolved = computed(() => route.name != null);

const isCrudRoute = computed(() => route.name === "actionrouter.listview" || route.name === "actionrouter.detailview");
const app = computed(() => route.params.app);
const model = computed(() => route.params.model);
const action = computed(() => route.params.action);
const pk = computed(() => route.params.pk);

// Model info is permission-filtered, so there is nothing to ask for without a session.
// Reading loggedIn synchronously keeps both computeds reactive to sign-in and sign-out.
// It matters most on sign-out: VUEDA empties its caches key by key, VueUse 14 flushes
// computedAsync synchronously, and an unguarded fetch here re-runs between two of those
// deletions and refills the cache VUEDA is still clearing, once per deletion.
const canFetchMetadata = computed(() => isCrudRoute.value && userStore.loggedIn);

// The view reports its own metadata failure. Here the cost is the verbose model name,
// and modelTitle already falls back to the model slug, so there is nothing more to say.
// VueUse 14 otherwise defaults onError to reportError, which logs an uncaught error.
const ignoreMetadataError = () => {};

const modelInfo = computedAsync(
    async () => {
        if (!canFetchMetadata.value) {
            return null;
        }
        return await modelInfoStore.fetchModelInfo({ app: app.value, model: model.value });
    },
    null,
    { onError: ignoreMetadataError },
);

const modelListTo = computedAsync(
    async () => {
        if (!canFetchMetadata.value) {
            return null;
        }
        return await getCRUDForTo({ app: app.value, model: model.value, view: "list" });
    },
    null,
    { onError: ignoreMetadataError },
);

const routeTitle = computed(
    () => route.meta?.titles?.view || route.meta?.title || memoizedStartCase(String(route.name || "")),
);
const appTitle = computed(() => memoizedStartCase(app.value || ""));
// storeModelInfo camelCases only nested sections (fields, filtering, expand); root keys such as
// verbose_name_plural keep the server's snake_case spelling. Django verbose names are lowercase, so
// title-case them the way ViewList titles its page ("List Purchase Orders").
const modelTitle = computed(() => memoizedStartCase(modelInfo.value?.verbose_name_plural || model.value || ""));

const actionTitle = computed(() => {
    if (action.value === "list") {
        return modelTitle.value;
    }
    if (action.value === "create") {
        return `New ${memoizedStartCase(modelInfo.value?.verbose_name || model.value || "")}`;
    }
    if (action.value === "read" && pk.value) {
        return `Record ${pk.value}`;
    }
    if (action.value === "update" && pk.value) {
        return `Edit ${pk.value}`;
    }
    if (action.value === "destroy" && pk.value) {
        return `Delete ${pk.value}`;
    }
    return memoizedStartCase(action.value || "");
});
</script>

<template>
    <Breadcrumb>
        <BreadcrumbList>
            <BreadcrumbItem>
                <BreadcrumbLink as-child>
                    <RouterLink :to="{ name: 'welcome' }">Warehouse</RouterLink>
                </BreadcrumbLink>
            </BreadcrumbItem>

            <template v-if="!routeResolved">
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                    <Skeleton class="h-4 w-16 align-middle" />
                </BreadcrumbItem>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                    <Skeleton class="h-4 w-24 align-middle" />
                </BreadcrumbItem>
            </template>

            <template v-else-if="isCrudRoute">
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                    <BreadcrumbPage v-if="action === 'list'">{{ appTitle }}</BreadcrumbPage>
                    <BreadcrumbLink v-else as-child>
                        <RouterLink :to="{ name: 'welcome' }">{{ appTitle }}</RouterLink>
                    </BreadcrumbLink>
                </BreadcrumbItem>

                <BreadcrumbSeparator />
                <BreadcrumbItem>
                    <BreadcrumbPage v-if="action === 'list'">{{ modelTitle }}</BreadcrumbPage>
                    <BreadcrumbLink v-else-if="unref(modelListTo)" as-child>
                        <RouterLink :to="unref(modelListTo)">{{ modelTitle }}</RouterLink>
                    </BreadcrumbLink>
                    <BreadcrumbPage v-else>{{ modelTitle }}</BreadcrumbPage>
                </BreadcrumbItem>

                <template v-if="action !== 'list'">
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                        <BreadcrumbPage>{{ actionTitle }}</BreadcrumbPage>
                    </BreadcrumbItem>
                </template>
            </template>

            <template v-else-if="route.name !== 'welcome'">
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                    <BreadcrumbPage>{{ routeTitle }}</BreadcrumbPage>
                </BreadcrumbItem>
            </template>
        </BreadcrumbList>
    </Breadcrumb>
</template>
