<script setup>
import PurchaseOrderFormFields from "@/form/PurchaseOrderFormFields.vue";
import { usePurchasePriceDefaults } from "@/use/usePurchasePriceDefaults.js";
import DefaultViewUpdate from "@/views/DefaultViewUpdate.vue";

defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
    pk: { type: [String, Number], required: true },
});
const attachPriceDefaults = usePurchasePriceDefaults();
</script>
<template>
    <DefaultViewUpdate :app="app" :model="model" :pk="pk" @form-context="attachPriceDefaults">
        <!-- The same layout as create, so the two forms do not drift apart. -->
        <template #fields="{ formModel, fieldNames }">
            <PurchaseOrderFormFields :field-names="fieldNames" :form-model="formModel" />
        </template>
    </DefaultViewUpdate>
</template>
