<script setup>
import { useRoute } from "vue-router";

import DefaultViewList from "@/views/DefaultViewList.vue";

const props = defineProps({ app: { type: String, required: true }, model: { type: String, required: true } });
defineOptions({ inheritAttrs: false });
const route = useRoute();
const filterables = [
    "reference",
    "supplier",
    "destination_warehouse",
    "order_date",
    "expected_arrival_date",
    "overdue",
    "is_open",
    "workflow_state",
];
</script>
<template>
    <DefaultViewList
        v-bind="{ ...props, ...$attrs }"
        :filterables="filterables"
        :params="route.query.replenishment_batch ? { replenishment_batch: route.query.replenishment_batch } : {}"
    >
        <template #before-list>
            <div
                v-if="route.query.replenishment_batch"
                class="flex items-center justify-between border-b px-4 py-2 text-sm"
            >
                <span>Orders created by this replenishment</span>
                <RouterLink :to="{ path: route.path, query: {} }" class="text-primary underline"
                    >Show all orders</RouterLink
                >
            </div>
        </template>
    </DefaultViewList>
</template>
