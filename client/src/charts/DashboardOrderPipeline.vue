<script setup>
import { useList } from "@arrai-innovations/reactive-helpers";
import Button from "@vueda/controls/button/Button.vue";
import NativeSelect from "@vueda/controls/native-select/NativeSelect.vue";
import Badge from "@vueda/display/badge/Badge.vue";
import Skeleton from "@vueda/feedback/skeleton/Skeleton.vue";
import { getCRUDForTo } from "@vueda/router/getCrud.js";
import Card from "@vueda/shell/card/Card.vue";
import CardContent from "@vueda/shell/card/CardContent.vue";
import CardDescription from "@vueda/shell/card/CardDescription.vue";
import CardHeader from "@vueda/shell/card/CardHeader.vue";
import CardTitle from "@vueda/shell/card/CardTitle.vue";
import { singlePagePaginatedListCrudAdaptor } from "@vueda/utils/listCrud.js";
import { computedAsync } from "@vueuse/core";
import { DateTime } from "luxon";
import { computed, onScopeDispose, reactive, ref } from "vue";
import { RouterLink } from "vue-router";

import ChartOrderPipeline from "@/charts/ChartOrderPipeline.vue";
import { pipelineParams } from "@/charts/purchasing.js";

const days = ref("30");
const today = ref(DateTime.utc().toISODate());
const params = computed(() => pipelineParams(days.value, DateTime.fromISO(today.value, { zone: "utc" })));
const report = useList({
    props: reactive({
        target: { app: "catalog", model: "purchaseorder", action: "pipeline" },
        pkKey: "id",
        params,
        intendToList: true,
    }),
    handlers: { list: singlePagePaginatedListCrudAdaptor },
});
onScopeDispose(report.stop);
const state = report.state;
const rows = computed(() =>
    state.loading !== false || state.errored
        ? []
        : state.objectsInOrder.map((row) => ({ ...row, count: row.order_count })),
);
const total = computed(() => rows.value.reduce((sum, row) => sum + row.count, 0));
const orderListRoute = computedAsync(
    () => getCRUDForTo({ app: "catalog", model: "purchaseorder", view: "list" }),
    null,
);
function refresh() {
    report.clearError();
    const next = DateTime.utc().toISODate();
    if (today.value !== next) today.value = next;
    else report.list();
}
</script>

<template>
    <section class="flex min-w-0 flex-col gap-3">
        <h2 class="text-muted-foreground text-xs font-semibold tracking-wide uppercase">Order pipeline</h2>
        <Card class="min-w-0">
            <CardHeader>
                <CardTitle class="text-sm font-medium">Purchase orders by state</CardTitle>
                <CardDescription
                    >Current states of orders placed in the selected period, including today.</CardDescription
                >
            </CardHeader>
            <CardContent class="flex flex-col gap-4">
                <div class="flex flex-wrap items-center gap-3">
                    <label for="pipeline-period" class="text-sm">Order date</label>
                    <NativeSelect id="pipeline-period" v-model="days">
                        <option value="30">Last 30 days</option>
                        <option value="90">Last 90 days</option>
                        <option value="all">All time</option>
                    </NativeSelect>
                    <Button emphasis="outline" :disabled="state.loading" @click="refresh">Refresh</Button>
                </div>
                <div v-if="state.errored" role="alert" class="flex items-center gap-3">
                    <p>The order pipeline could not be loaded.</p>
                    <Button emphasis="outline" @click="refresh">Retry</Button>
                </div>
                <div v-else-if="state.loading !== false" role="status" aria-label="Loading the order pipeline">
                    <Skeleton class="h-56" />
                </div>
                <template v-else>
                    <p class="text-muted-foreground text-sm" role="status">
                        {{ total ? `${total} orders in this period` : "No orders placed in this period." }}
                    </p>
                    <ChartOrderPipeline :states="rows" />
                    <ul class="flex flex-wrap items-baseline gap-x-5 gap-y-2 text-sm">
                        <li v-for="row in rows" :key="row.code" class="flex items-baseline gap-2">
                            <RouterLink
                                v-if="row.count && orderListRoute"
                                :to="{ ...orderListRoute, query: { ...params, workflow_state: String(row.id) } }"
                                class="text-primary-text hover:text-primary-text-active underline-offset-4 hover:underline"
                                >{{ row.name }}</RouterLink
                            >
                            <span v-else class="text-muted-foreground">{{ row.name }}</span>
                            <Badge numeric variant="outline">{{ row.count }}</Badge>
                        </li>
                    </ul>
                </template>
            </CardContent>
        </Card>
    </section>
</template>
