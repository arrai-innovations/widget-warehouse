<script setup>
import { usePurchasePriceDefaults } from "@/use/usePurchasePriceDefaults.js";
import DefaultViewUpdate from "@/views/DefaultViewUpdate.vue";

defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
    pk: { type: [String, Number], required: true },
});
const attachPriceDefaults = usePurchasePriceDefaults();
</script>
<!-- The field layout comes from formLayouts.js through DefaultViewUpdate. -->
<template><DefaultViewUpdate :app="app" :model="model" :pk="pk" @form-context="attachPriceDefaults" /></template>
