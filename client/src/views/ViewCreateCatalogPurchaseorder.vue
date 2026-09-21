<script setup>
import ViewCreate from "@vueda/views/ViewCreate.vue";

import PurchaseOrderFormFields from "@/form/PurchaseOrderFormFields.vue";
import { usePurchasePriceDefaults } from "@/use/usePurchasePriceDefaults.js";

defineProps({ app: { type: String, required: true }, model: { type: String, required: true } });
const attachPriceDefaults = usePurchasePriceDefaults();
</script>
<template>
    <ViewCreate :app="app" :model="model" @form-context="attachPriceDefaults">
        <!-- The fields slot replaces FormModel's default one-field-per-row loop. -->
        <template #fields="{ formModel, fieldNames }">
            <PurchaseOrderFormFields :field-names="fieldNames" :form-model="formModel" />
        </template>
    </ViewCreate>
</template>
