<script setup>
import {
    PhCalendarCheck,
    PhClockCountdown,
    PhFileArrowUp,
    PhGear,
    PhGitBranch,
    PhHandshake,
    PhSealQuestion,
    PhStackMinus,
    PhWarehouse,
} from "@phosphor-icons/vue";
import Badge from "@vueda/display/badge/Badge.vue";
import Skeleton from "@vueda/feedback/skeleton/Skeleton.vue";
import { getCRUDForTo } from "@vueda/router/getCrud.js";
import Card from "@vueda/shell/card/Card.vue";
import CardContent from "@vueda/shell/card/CardContent.vue";
import CardDescription from "@vueda/shell/card/CardDescription.vue";
import CardHeader from "@vueda/shell/card/CardHeader.vue";
import CardTitle from "@vueda/shell/card/CardTitle.vue";
import { storeModelInfo } from "@vueda/stores/storeModelInfo.js";
import { storeUser } from "@vueda/stores/storeUser.js";
import { usePageTitle } from "@vueda/use/usePageTitle.js";
import { PAGE_SIZE_PARAM } from "@vueda/utils/constants.js";
import { fetchHelper } from "@vueda/utils/fetchSupport.js";
import { getListUrl } from "@vueda/utils/urls.js";
import { computedAsync } from "@vueuse/core";
import { computed, markRaw, unref } from "vue";
import { RouterLink } from "vue-router";

const modelInfoStore = storeModelInfo();
const userStore = storeUser();

usePageTitle(() => ({ title: "Dashboard" }));

const APP = "catalog";
const PIPELINE_MODEL = "purchaseorderstatecount";

// Today, as the server's date filters want it. The count request and the link the tile
// points at use the same value, so the list a reader lands on cannot disagree with the
// number that sent them there.
const today = new Date().toISOString().slice(0, 10);

// Tiles are declared here rather than in setupModelConfig.js. Model config customizes how
// VUEDA renders a model wherever that model appears, which is a different job: a tile is
// this page's content, not a property of the model it counts.
//
// Every tile is the same shape on purpose. `params` is sent to the list endpoint to get
// the count and handed to the link as the route query, so the list a reader lands on is
// filtered by exactly what was counted. VUEDA's list view restores its filters from the
// query, and a filter's query name is its API name, so one object does both jobs.
//
// Nothing here is chosen by role. A tile whose model the signed-in user cannot list is
// dropped after the server says so, which is the whole of the per-role difference on this
// page: the sales roles lose the orders and suppliers, the inventory roles lose the
// promotions, and no code on this page asks who anybody is.
const queues = [
    {
        key: "restock",
        title: "Below reorder",
        description: "Stock under its own threshold",
        model: "inventoryrecord",
        params: { below_reorder: "true" },
        icon: PhStackMinus,
    },
    {
        key: "overdue",
        title: "Overdue arrivals",
        description: "Ordered stock past its expected date",
        model: "purchaseorder",
        params: { overdue: "true" },
        icon: PhClockCountdown,
    },
    {
        key: "review",
        title: "Suppliers under review",
        description: "Neither approved nor rejected",
        model: "supplier",
        params: { under_review: "true" },
        icon: PhSealQuestion,
    },
    {
        key: "promotions",
        title: "Promotions running",
        description: "Inside their valid date range today",
        model: "promotion",
        params: { active_on: today },
        icon: PhCalendarCheck,
    },
];

// The same shape again, with no filter: how much of each thing exists. These make the app
// look inhabited rather than demonstrating anything, so they are smaller and quieter.
const scale = [
    { key: "widgets", title: "Widgets", model: "widget", params: {}, icon: PhGear },
    { key: "variants", title: "Variants", model: "widgetvariant", params: {}, icon: PhGitBranch },
    { key: "suppliers", title: "Suppliers", model: "supplier", params: {}, icon: PhHandshake },
    { key: "warehouses", title: "Warehouses", model: "warehouse", params: {}, icon: PhWarehouse },
    { key: "orders", title: "Purchase orders", model: "purchaseorder", params: {}, icon: PhFileArrowUp },
];

function queryString(params) {
    return `?${new URLSearchParams(params).toString()}`;
}

async function mayList(model) {
    // Model info reports only the actions this user is permitted, so this is the server's
    // own permission answer rather than a guess made from the signed-in role.
    const info = await modelInfoStore.fetchModelInfo({ app: APP, model });
    return Boolean(info.actions?.some((action) => action.name === "list"));
}

/**
 * Resolve one tile: may this user see it, how many rows match, and where does it point.
 *
 * Three states, the same three the sidebar uses: `undefined` while resolving, `null` for a
 * model this user cannot list, and an object once it has a number.
 */
function resolveTile({ model, params }) {
    return computedAsync(async () => {
        // Read synchronously so this re-evaluates on sign-in. Fetching model info while
        // logged out would also cache a 403 in the info store's error guard, leaving the
        // page on skeletons until a reload.
        if (!userStore.loggedIn) {
            return undefined;
        }
        if (!(await mayList(model))) {
            return null;
        }
        // One row, because only the envelope matters: every VUEDA list response carries
        // totalRecords for the whole filtered set, so a count costs a page of one rather
        // than a bespoke endpoint.
        const query = queryString({ ...params, [PAGE_SIZE_PARAM]: 1 });
        const page = await fetchHelper(getListUrl({ app: APP, model, query }), {}, `Counting ${model}`);
        return {
            count: page.totalRecords,
            to: await getCRUDForTo({ app: APP, model, view: "list", query: params }),
        };
    });
}

function withResolution(tiles) {
    return tiles.map(({ icon, ...tile }) => ({
        ...tile,
        // The icon is a component, so keep it out of the reactive proxy the way VUEDA's
        // own icon registry does.
        icon: markRaw(icon),
        state: resolveTile(tile),
    }));
}

const queueTiles = withResolution(queues);
const scaleTiles = withResolution(scale);

// The pipeline is one request for the whole band. The counts come from a database view
// with a row per state, so a state holding no orders is a zero rather than a missing bar,
// and the response's column total is every order in one number.
const pipeline = computedAsync(async () => {
    if (!userStore.loggedIn) {
        return undefined;
    }
    if (!(await mayList(PIPELINE_MODEL))) {
        return null;
    }
    const query = queryString({ [PAGE_SIZE_PARAM]: 20 });
    const page = await fetchHelper(getListUrl({ app: APP, model: PIPELINE_MODEL, query }), {}, "Counting the pipeline");
    const rows = page.results ?? [];
    // Scaled against the busiest state rather than the total, so the shortest bar is still
    // visible. The number beside each bar is the value; the bar is the comparison.
    const busiest = Math.max(1, ...rows.map((row) => row.order_count));
    const linkable = await mayList("purchaseorder");
    return {
        total: page.columnTotals?.order_count ?? 0,
        states: await Promise.all(
            rows.map(async (row) => ({
                code: row.code,
                name: row.name,
                count: row.order_count,
                share: row.order_count / busiest,
                // A state with no orders does not link. The workflow state filter only
                // accepts states some row is currently in, so a link from an empty bar
                // would land on a 400 rather than an empty list.
                to:
                    linkable && row.order_count
                        ? await getCRUDForTo({
                              app: APP,
                              model: "purchaseorder",
                              view: "list",
                              query: { workflow_state: String(row.state) },
                          })
                        : null,
            })),
        ),
    };
});

// loggedInUser, not user: the who-is response lands there, and reading the wrong one is
// a silent fallback to the generic greeting rather than an error.
const greeting = computed(() => userStore.loggedInUser?.name || userStore.loggedInUser?.email || "there");
</script>

<template>
    <div class="flex flex-col gap-8 p-6">
        <header class="flex flex-col gap-1">
            <h1 class="text-2xl font-semibold">Welcome, {{ greeting }}</h1>
            <p class="text-muted-foreground text-sm">
                Everything below is what your account may list. No part of this page is chosen by role.
            </p>
        </header>

        <section class="flex flex-col gap-3">
            <h2 class="text-muted-foreground text-xs font-semibold tracking-wide uppercase">Needs attention</h2>
            <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <template v-for="tile in queueTiles" :key="tile.key">
                    <Skeleton v-if="unref(tile.state) === undefined" class="h-32" />
                    <!-- A column with the number pushed to the bottom, so a tile whose
                         description wraps to two lines still lines its value up with the
                         tiles beside it. -->
                    <Card v-else-if="unref(tile.state)" class="flex flex-col overflow-hidden">
                        <CardHeader>
                            <CardTitle class="flex items-center gap-2 text-sm font-medium">
                                <component :is="tile.icon" weight="duotone" class="size-4 shrink-0" />
                                {{ tile.title }}
                            </CardTitle>
                            <CardDescription>{{ tile.description }}</CardDescription>
                        </CardHeader>
                        <CardContent class="mt-auto flex items-end justify-between gap-3">
                            <span
                                class="text-3xl font-semibold"
                                :class="unref(tile.state).count ? 'text-foreground' : 'text-muted-foreground'"
                            >
                                {{ unref(tile.state).count }}
                            </span>
                            <RouterLink
                                :to="unref(tile.state).to"
                                class="text-primary-text hover:text-primary-text-active text-sm underline-offset-4 hover:underline"
                            >
                                Open list
                            </RouterLink>
                        </CardContent>
                    </Card>
                </template>
            </div>
        </section>

        <section v-if="unref(pipeline) !== null" class="flex flex-col gap-3">
            <h2 class="text-muted-foreground text-xs font-semibold tracking-wide uppercase">Order pipeline</h2>
            <Skeleton v-if="unref(pipeline) === undefined" class="h-56" />
            <Card v-else>
                <CardHeader>
                    <CardTitle class="text-sm font-medium">Purchase orders by state</CardTitle>
                    <CardDescription>
                        {{ unref(pipeline).total }} orders, counted in one request by a database view rather than one
                        request per state.
                    </CardDescription>
                </CardHeader>
                <CardContent class="flex flex-col gap-3">
                    <div v-for="state in unref(pipeline).states" :key="state.code" class="flex flex-col gap-1">
                        <div class="flex items-baseline justify-between gap-3 text-sm">
                            <RouterLink
                                v-if="state.to"
                                :to="state.to"
                                class="text-primary-text hover:text-primary-text-active underline-offset-4 hover:underline"
                            >
                                {{ state.name }}
                            </RouterLink>
                            <span v-else class="text-muted-foreground">{{ state.name }}</span>
                            <Badge numeric variant="outline">{{ state.count }}</Badge>
                        </div>
                        <div class="bg-muted h-2 w-full overflow-hidden rounded-full">
                            <div
                                class="bg-primary h-full rounded-r-[4px]"
                                :style="{ width: `${Math.round(state.share * 100)}%` }"
                            />
                        </div>
                    </div>
                </CardContent>
            </Card>
        </section>

        <section class="flex flex-col gap-3">
            <h2 class="text-muted-foreground text-xs font-semibold tracking-wide uppercase">In the warehouse</h2>
            <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
                <template v-for="tile in scaleTiles" :key="tile.key">
                    <Skeleton v-if="unref(tile.state) === undefined" class="h-20" />
                    <Card v-else-if="unref(tile.state)">
                        <CardContent class="flex flex-col gap-1 py-4">
                            <span class="text-muted-foreground flex items-center gap-2 text-xs">
                                <component :is="tile.icon" weight="duotone" class="size-4 shrink-0" />
                                {{ tile.title }}
                            </span>
                            <RouterLink :to="unref(tile.state).to" class="text-xl font-semibold hover:underline">
                                {{ unref(tile.state).count }}
                            </RouterLink>
                        </CardContent>
                    </Card>
                </template>
            </div>
        </section>
    </div>
</template>
