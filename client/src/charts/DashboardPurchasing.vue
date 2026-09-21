<script setup>
import { useList } from "@arrai-innovations/reactive-helpers";
import Button from "@vueda/controls/button/Button.vue";
import NativeSelect from "@vueda/controls/native-select/NativeSelect.vue";
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

import ChartSupplierPurchasing from "@/charts/ChartSupplierPurchasing.vue";
import {
    amountFormat,
    chartRows,
    purchasingParams,
    supplierStyle,
    weekFormat,
    weekQuery,
} from "@/charts/purchasing.js";

const weeks = ref("12");
const refreshDate = ref(DateTime.utc().toISODate());
const params = computed(() => purchasingParams(weeks.value, DateTime.fromISO(refreshDate.value, { zone: "utc" })));
const report = useList({
    props: reactive({
        target: { app: "catalog", model: "purchaseorder", action: "purchasing_trend" },
        pkKey: "id",
        params,
        intendToList: true,
    }),
    handlers: { list: singlePagePaginatedListCrudAdaptor },
});
onScopeDispose(report.stop);
const state = report.state;
const hidden = ref(new Set());
// The adapter clears membership before replacing rows. Do not derive chart data
// during that transition, or present previous values under the new period.
const suppliers = computed(() =>
    state.loading !== false || state.errored
        ? []
        : state.objectsInOrder.map((row) => ({ ...row, ...supplierStyle(row.code) })),
);
const visible = computed(() => suppliers.value.filter((supplier) => !hidden.value.has(supplier.id)));
const rows = computed(() => chartRows(visible.value));
// Resolve the route once; derive each link's query synchronously from its displayed
// week and supplier, so a refreshed table never briefly inherits previous link dates.
const orderListRoute = computedAsync(
    () => getCRUDForTo({ app: "catalog", model: "purchaseorder", view: "list" }),
    null,
);
function toggle(id) {
    const next = new Set(hidden.value);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    hidden.value = next;
}
function refresh() {
    // The adapter clears old rows when a request starts, so refreshed values are never
    // presented under a different period. useList cancels superseded requests/unmounts.
    report.clearError();
    const today = DateTime.utc().toISODate();
    if (refreshDate.value !== today) refreshDate.value = today;
    else report.list();
}
</script>

<template>
    <section class="flex min-w-0 flex-col gap-3">
        <h2 class="text-muted-foreground text-xs font-semibold tracking-wide uppercase">Supplier purchasing</h2>
        <Card class="unovis-vueda min-w-0">
            <CardHeader>
                <CardTitle class="text-sm font-medium">Weekly purchase order value by supplier</CardTitle>
                <CardDescription
                    >Approved and received orders, grouped by order date. Complete Monday-to-Sunday
                    weeks.</CardDescription
                >
            </CardHeader>
            <CardContent class="flex min-w-0 flex-col gap-4">
                <div class="flex flex-wrap items-center gap-3">
                    <label for="purchasing-period" class="text-sm">Reporting period</label>
                    <NativeSelect id="purchasing-period" v-model="weeks">
                        <option value="6">Last 6 complete weeks</option>
                        <option value="12">Last 12 complete weeks</option>
                        <option value="26">Last 26 complete weeks</option>
                    </NativeSelect>
                    <Button emphasis="outline" :disabled="state.loading" @click="refresh">Refresh</Button>
                </div>
                <div v-if="state.errored" role="alert" class="flex items-center gap-3">
                    <p>Purchasing data could not be loaded.</p>
                    <Button emphasis="outline" @click="refresh">Retry</Button>
                </div>
                <div v-else-if="state.loading !== false" role="status" aria-label="Loading purchasing data">
                    <Skeleton class="h-80" />
                </div>
                <p v-else-if="!suppliers.length" role="status" class="text-muted-foreground text-sm">
                    No approved or received purchasing in this period.
                </p>
                <template v-else>
                    <div
                        class="flex flex-wrap items-center gap-2"
                        role="group"
                        aria-label="Suppliers shown in the chart"
                    >
                        <Button
                            v-for="supplier in suppliers"
                            :key="supplier.id"
                            size="sm"
                            emphasis="ghost"
                            :aria-pressed="!hidden.has(supplier.id)"
                            :class="hidden.has(supplier.id) ? 'opacity-50' : ''"
                            @click="toggle(supplier.id)"
                        >
                            <svg width="30" height="12" style="width: 30px; height: 12px" aria-hidden="true">
                                <line
                                    x1="0"
                                    x2="30"
                                    y1="6"
                                    y2="6"
                                    :stroke="supplier.color"
                                    stroke-width="2.5"
                                    :stroke-dasharray="supplier.dash.join(' ') || 'none'"
                                />
                            </svg>
                            {{ supplier.name }}
                        </Button>
                    </div>
                    <ChartSupplierPurchasing v-if="visible.length" :series="visible" />
                    <p v-else role="status" class="text-muted-foreground text-sm">
                        Select a supplier to show its purchasing.
                    </p>
                    <details v-if="visible.length">
                        <summary class="cursor-pointer text-sm font-medium">View values and purchase orders</summary>
                        <div class="mt-3 overflow-x-auto">
                            <table class="w-full text-right text-sm tabular-nums">
                                <caption class="text-muted-foreground mb-2 text-left text-xs">
                                    Order value by week. Each amount links to its matching orders. No currency is
                                    recorded in this catalog.
                                </caption>
                                <thead>
                                    <tr class="border-border border-b">
                                        <th scope="col" class="p-2 text-left">Week starting</th>
                                        <th v-for="supplier in visible" :key="supplier.id" scope="col" class="p-2">
                                            {{ supplier.name }}
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="row in rows" :key="row.week" class="border-border border-b">
                                        <th scope="row" class="p-2 text-left font-normal whitespace-nowrap">
                                            {{ weekFormat.format(row.timestamp) }}
                                        </th>
                                        <td v-for="supplier in visible" :key="supplier.id" class="p-2">
                                            <RouterLink
                                                v-if="row[supplier.id] && orderListRoute"
                                                :to="{ ...orderListRoute, query: weekQuery(row.week, supplier.id) }"
                                                class="text-primary-text underline-offset-4 hover:underline"
                                                >{{ amountFormat.format(row.amounts[supplier.id]) }}</RouterLink
                                            >
                                            <span v-else>{{ amountFormat.format(row.amounts[supplier.id]) }}</span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </details>
                </template>
            </CardContent>
        </Card>
    </section>
</template>
