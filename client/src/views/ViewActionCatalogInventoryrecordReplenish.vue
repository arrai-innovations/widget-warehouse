<script setup>
import { toast } from "@arrai-innovations/vue-sonner";
import Button from "@vueda/controls/button/Button.vue";
import { getCRUDForTo } from "@vueda/router/getCrud.js";
import { useForm } from "@vueda/use/useForm.js";
import { usePageTitle } from "@vueda/use/usePageTitle.js";
import { actionRequestHeaders, fetchHelper, readActionResponse } from "@vueda/utils/fetchSupport.js";
import { getListUrl } from "@vueda/utils/urls.js";
import ActionForm from "@vueda/views/ActionForm.vue";
import { computed, reactive, watch } from "vue";
import { useRouter } from "vue-router";

const props = defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
    pk: { type: [String, Number, Array], default: undefined },
});
const router = useRouter();
usePageTitle(() => ({ title: "Replenish inventory" }));
const initial = reactive({ initialValues: { lines: [] } });
const form = useForm(initial);
const fetchState = reactive({ loading: true, error: null, errored: false });
let batchId = crypto.randomUUID();
const url = () => getListUrl({ app: props.app, model: props.model, action: "replenish" });
const rows = computed(() => form.state.values.lines || []);
const selected = computed(() => rows.value.filter((row) => row.included && !row.issue));
const groups = computed(() => {
    const result = new Map();
    rows.value.forEach((row, index) => {
        const key = `${row.supplier_id}:${row.warehouse_id}`;
        if (!result.has(key)) result.set(key, { key, supplier: row.supplier, warehouse: row.warehouse, rows: [] });
        result.get(key).rows.push({ ...row, index });
    });
    return [...result.values()];
});
const orderCount = computed(() => new Set(selected.value.map((row) => `${row.supplier_id}:${row.warehouse_id}`)).size);
const total = computed(() =>
    selected.value.reduce((sum, row) => sum + Number(row.quantity || 0) * Number(row.unit_price || 0), 0),
);
const money = new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
let generation = 0;
async function load() {
    const current = ++generation;
    fetchState.loading = true;
    fetchState.error = null;
    fetchState.errored = false;
    try {
        const pks = Array.isArray(props.pk)
            ? props.pk
            : String(props.pk || "")
                  .split(",")
                  .filter(Boolean);
        const result = await fetchHelper(`${url()}?${new URLSearchParams({ pks: pks.join(",") })}`);
        if (current !== generation) return;
        batchId = crypto.randomUUID();
        initial.initialValues = { lines: result.rows.map((row) => ({ ...row, included: !row.issue })) };
    } catch (error) {
        if (current !== generation) return;
        fetchState.error = error;
        fetchState.errored = true;
    } finally {
        if (current === generation) fetchState.loading = false;
    }
}
watch(() => props.pk, load, { immediate: true });
function update(index, field, value) {
    form.updateValue(`lines.${index}.${field}`, value);
    // Submitted rows omit unchecked proposals, so server array indexes can differ
    // from display indexes. Revalidate the complete selection after an edit.
    for (const name of Object.keys(form.state.errors)) form.clearServerErrors(name);
}
async function runAction({ formValues, dryRun, acknowledgeWarnings }) {
    const lines = formValues.lines
        .filter((row) => row.included && !row.issue)
        .map((row) => ({
            inventory_id: row.inventory_id,
            quantity: row.quantity,
            unit_price: row.unit_price,
            snapshot: row.snapshot,
        }));
    return readActionResponse(
        await fetch(url(), {
            method: "POST",
            credentials: "include",
            headers: actionRequestHeaders({ dryRun, acknowledgeWarnings }),
            body: JSON.stringify({ batch_id: batchId, lines }),
        }),
        { messagePrefix: "Could not create replenishment orders", bulk: true },
    );
}
async function success(result) {
    toast.success(`Created ${result.orders.length} draft purchase ${result.orders.length === 1 ? "order" : "orders"}`);
    await router.push(
        await getCRUDForTo({
            app: "catalog",
            model: "purchaseorder",
            view: "list",
            query: { replenishment_batch: result.batch_id },
        }),
    );
}
async function cancel() {
    await router.push(
        await getCRUDForTo({ app: props.app, model: props.model, view: "list", query: { below_reorder: "true" } }),
    );
}
</script>

<template>
    <div class="p-4">
        <ActionForm
            :run-action="runAction"
            :fetch-state="fetchState"
            :has-input="true"
            :require-modified="false"
            :on-submission-success-handler="success"
            :redirect-to="cancel"
            action-error-summary="Could not create purchase orders"
        >
            <template #action-form-inner="{ loading }">
                <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
                    <p class="max-w-3xl text-sm text-muted-foreground">
                        Review quantities and purchase prices before creating drafts. Targets use maximum stock levels,
                        or the reorder threshold when no maximum is set. Incoming is approved; pending is still awaiting
                        approval.
                    </p>
                    <Button type="button" emphasis="ghost" :disabled="loading" @click="load">Reload proposals</Button>
                </div>
                <fieldset :disabled="loading" class="flex min-w-0 flex-col gap-5">
                    <section v-for="group in groups" :key="group.key" class="rounded border">
                        <h2 class="border-b bg-muted px-3 py-2 font-semibold">
                            {{ group.supplier }} · {{ group.warehouse }}
                        </h2>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-sm">
                                <thead>
                                    <tr class="border-b text-muted-foreground">
                                        <th class="p-3">Include / Stock item</th>
                                        <th class="p-3">On hand</th>
                                        <th class="p-3">Threshold / Target</th>
                                        <th class="p-3">Incoming / Pending</th>
                                        <th class="p-3">Order quantity</th>
                                        <th class="p-3">Unit price</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr
                                        v-for="row in group.rows"
                                        :key="row.inventory_id"
                                        class="border-b last:border-0"
                                    >
                                        <td class="p-3 min-w-64">
                                            <label class="flex items-center gap-2"
                                                ><input
                                                    type="checkbox"
                                                    :checked="row.included"
                                                    :disabled="!!row.issue"
                                                    @change="update(row.index, 'included', $event.target.checked)"
                                                />{{ row.name }}</label
                                            >
                                            <p class="mt-1 text-xs text-muted-foreground">{{ row.product }}</p>
                                            <p v-if="row.issue" class="mt-1 text-sm text-warning">{{ row.issue }}</p>
                                        </td>
                                        <td class="p-3">{{ row.on_hand }}</td>
                                        <td class="p-3">{{ row.threshold }} / {{ row.target }}</td>
                                        <td class="p-3">{{ row.incoming }} / {{ row.pending }}</td>
                                        <td class="p-3">
                                            <input
                                                type="number"
                                                min="1"
                                                step="1"
                                                :value="row.quantity"
                                                :aria-label="`Order quantity for ${row.name}`"
                                                :disabled="!!row.issue || !row.included"
                                                :required="row.included && !row.issue"
                                                class="w-24 rounded border bg-background p-2"
                                                @input="update(row.index, 'quantity', $event.target.value)"
                                            />
                                        </td>
                                        <td class="p-3">
                                            <input
                                                type="number"
                                                min="0"
                                                step="0.01"
                                                :value="row.unit_price"
                                                :aria-label="`Unit price for ${row.name}`"
                                                :disabled="!!row.issue || !row.included"
                                                :required="row.included && !row.issue"
                                                class="w-28 rounded border bg-background p-2"
                                                @input="update(row.index, 'unit_price', $event.target.value)"
                                            />
                                            <p v-if="row.unit_price == null" class="text-xs text-muted-foreground">
                                                No supplier cost. Enter a price.
                                            </p>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </section>
                </fieldset>
                <p v-if="!fetchState.loading && !rows.length && !fetchState.errored" class="py-4">
                    Select inventory records from the list first.
                </p>
                <p class="my-4 font-medium">
                    {{ selected.length }} lines · {{ orderCount }} draft {{ orderCount === 1 ? "order" : "orders" }} ·
                    Total {{ money.format(total) }}
                </p>
            </template>
            <template #confirm-button="slotProps">
                <Button
                    v-bind="slotProps"
                    :disabled="slotProps.disabled || slotProps.loading || !selected.length || fetchState.errored"
                    >Create {{ orderCount }} draft purchase {{ orderCount === 1 ? "order" : "orders" }}</Button
                >
            </template>
        </ActionForm>
    </div>
</template>
